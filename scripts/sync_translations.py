#!/usr/bin/env python3
"""从 wgmods/ModSDK 拉取三语言翻译文件并按版本号快照 + 反编译为 .po

目录结构:
    translations/<版本号>/zh/global.mo + global.po
    translations/<版本号>/zh-sg/global.mo + global.po
    translations/<版本号>/en/global.mo + global.po
旧版本永远保留。
"""
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

import polib

REPO = "wgmods/ModSDK"
REMOTE = f"https://github.com/{REPO}.git"
API_TAGS = f"https://api.github.com/repos/{REPO}/tags"
LANGS = ["zh", "zh-sg", "en"]
MO_PATH_TMPL = "global.mo/{lang}/LC_MESSAGES/global.mo"
TRANSLATIONS_DIR = Path("translations")

MAGIC_LE = b"\xde\x12\x04\x95"  # 0x950412de 小端
MAGIC_BE = b"\x95\x04\x12\xde"  # 大端

# gettext .po 头部的标准字段名（用于修复挤成一行的元数据）
META_FIELDS = [
    b"Project-Id-Version:", b"Report-Msgid-Bugs-To:", b"POT-Creation-Date:",
    b"PO-Revision-Date:", b"Last-Translator:", b"Language-Team:", b"Language:",
    b"MIME-Version:", b"Content-Type:", b"Content-Transfer-Encoding:",
    b"Plural-Forms:", b"X-Generator:", b"#-#-#-#-#",
]


def fix_meta_newlines(meta: bytes) -> bytes:
    """wgmods 的 .mo 元数据换行符全部丢失，字段挤成一行，
    导致 gettext 无法按行解析 Content-Type / charset。
    此函数在每个标准字段名前补上换行，拆成标准多行结构。"""
    positions = []
    for f in META_FIELDS:
        start = 0
        while True:
            idx = meta.find(f, start)
            if idx == -1:
                break
            if idx == 0 or meta[idx - 1:idx] != b"\n":
                positions.append(idx)
            start = idx + len(f)
    positions = sorted(set(positions))
    if not positions:
        return meta
    result = bytearray()
    prev = 0
    for pos in positions:
        seg = meta[prev:pos]
        if result and seg and not seg.endswith(b"\n"):
            result += b"\n"
        result += seg
        prev = pos
    result += meta[prev:]
    return bytes(result)


def normalize_charset(meta: bytes) -> bytes:
    """把 charset 行规范化为干净的一行，避免行尾残留字符
    （如 'charset=utf-8)  #-#-#-#-#'）导致编码名解析失败。"""
    lines = meta.split(b"\n")
    out = []
    for line in lines:
        if b"charset=" in line:
            out.append(b"Content-Type: text/plain; charset=UTF-8")
        else:
            out.append(line)
    return b"\n".join(out)


def fix_mo_header(data: bytes) -> bytes:
    """完整修复混乱的 .mo 文件头，返回可被 gettext/polib 解析的 .mo 数据。

    修复内容:
      1. 若 magic number 不在文件开头，搜索并截掉前面的垃圾字节
      2. 修复丢失换行的元数据（字段挤成一行的问题）
      3. 规范化 charset 声明行
      4. 重写第 0 条 msgstr 的 (长度, 偏移) 并追加新元数据
    """
    # 1. 定位 magic number
    if data[:4] not in (MAGIC_LE, MAGIC_BE):
        for magic in (MAGIC_LE, MAGIC_BE):
            idx = data.find(magic)
            if idx > 0:
                print(f"  [文件头修复] 在偏移 {idx} 处找到 magic number，截断垃圾数据")
                data = data[idx:]
                break
    if data[:4] == MAGIC_LE:
        fmt = "<"
    elif data[:4] == MAGIC_BE:
        fmt = ">"
    else:
        raise ValueError("无法在文件中定位 .mo magic number，文件可能已损坏")

    magic, rev, n, o, t, s, h = struct.unpack_from(fmt + "IIIIIII", data, 0)

    # 2. 读取第 0 条 msgstr（元数据）并修复
    t_ln, t_so = struct.unpack_from(fmt + "II", data, t)
    meta = data[t_so:t_so + t_ln]
    new_meta = normalize_charset(fix_meta_newlines(meta))
    if new_meta == meta:
        return data  # 无需修改

    # 3. 更新 T 表第 0 条 (length, offset) 指向文件末尾的新元数据
    out = bytearray(data)
    new_off = len(out)
    struct.pack_into(fmt + "II", out, t, len(new_meta), new_off)
    out += new_meta
    out += b"\x00"  # 尾部填充，保证 tend < buflen（gettext 的边界检查要求严格小于）
    print(f"  [文件头修复] 元数据已重建: {len(meta)} -> {len(new_meta)} 字节")
    return bytes(out)


def get_latest_tag(token: str | None) -> str | None:
    """通过 GitHub API 获取仓库最新 tag"""
    req = urllib.request.Request(API_TAGS, headers={"User-Agent": "wows-zh-shipname-fixes"})
    if token:
        req.add_header("Authorization", f"token {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        tags = json.load(resp)
    if not tags:
        return None
    return tags[0]["name"]


def fetch_mo(tag: str, workdir: Path) -> dict[str, Path]:
    """用 sparse clone 只拉取指定 tag 的 global.mo 目录"""
    tmp = workdir / "modsdk_tmp"
    subprocess.run(
        ["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse",
         "--branch", tag, REMOTE, str(tmp)],
        check=True, capture_output=True, text=True,
    )
    subprocess.run(
        ["git", "sparse-checkout", "set", "global.mo"],
        cwd=tmp, check=True, capture_output=True, text=True,
    )
    result = {}
    for lang in LANGS:
        src = tmp / MO_PATH_TMPL.format(lang=lang)
        if src.exists():
            result[lang] = src
        else:
            print(f"  [警告] {lang} 的 mo 文件不存在: {src}")
    shutil.rmtree(tmp, ignore_errors=True)
    return result


def decompile(mo_path: Path, po_path: Path) -> None:
    """修复文件头并用 polib 反编译 .mo -> .po"""
    data = mo_path.read_bytes()
    data = fix_mo_header(data)
    tmp_mo = mo_path.with_suffix(".fixed.mo")
    tmp_mo.write_bytes(data)
    try:
        po = polib.mofile(str(tmp_mo))
        po.save_as_pofile(str(po_path))
        print(f"  [反编译] {mo_path.name} -> {po_path.name} ({len(po)} 条)")
    except Exception as e:
        raise RuntimeError(f"反编译失败 {mo_path}: {e}") from e
    finally:
        tmp_mo.unlink(missing_ok=True)


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN", "") or None

    print(f"查询 {REPO} 最新 tag ...")
    tag = get_latest_tag(token)
    if not tag:
        print("未获取到最新 tag")
        return 1
    print(f"最新版本: {tag}")

    out_dir = TRANSLATIONS_DIR / tag
    if out_dir.exists():
        print(f"版本 {tag} 已同步过，跳过")
        return 0

    print(f"拉取版本 {tag} 的翻译文件 ...")
    with tempfile.TemporaryDirectory() as td:
        mos = fetch_mo(tag, Path(td))
        if not mos:
            print("没有获取到任何 mo 文件，终止")
            return 1
        for lang, mo_path in mos.items():
            lang_dir = out_dir / lang
            lang_dir.mkdir(parents=True, exist_ok=True)
            dst_mo = lang_dir / "global.mo"
            shutil.copy(mo_path, dst_mo)
            decompile(dst_mo, lang_dir / "global.po")

    (out_dir / "README.md").write_text(
        f"# 版本 {tag}\n\n"
        f"ModSDK 翻译文件快照，来源: {REPO} 标签 `{tag}`。\n"
        f"目录下为三种语言的原始 .mo 与反编译的 .po 文件。\n",
        encoding="utf-8",
    )
    print(f"完成: 已保存到 {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
