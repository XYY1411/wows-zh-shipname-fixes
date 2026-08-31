#!/usr/bin/env python3
"""从 wgmods/ModSDK 拉取三语言翻译文件并按版本号快照 + 反编译为 .po

目录结构:
    translations/<版本号>/zh/global.mo + global.po
    translations/<版本号>/zh_sg/global.mo + global.po
    translations/<版本号>/en/global.mo + global.po
旧版本永远保留。

说明:
  - 拉取方式: 直接用 GitHub raw URL 下载三个 .mo 文件
    (sparse checkout 在 partial clone 环境下不可靠, 已弃用)
  - ModSDK 实际语言目录: zh / zh_sg / en (注意 zh_sg 是下划线!)
"""
import csv
import json
import os
import re
import shutil
import struct
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import polib

REPO = "wgmods/ModSDK"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}"
API_TAGS = f"https://api.github.com/repos/{REPO}/tags"
# 注意: ModSDK 的语言目录是 zh_sg(下划线), 不是 zh-sg(连字符)
LANGS = ["zh", "zh_sg", "en"]
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
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            tags = json.load(resp)
    except urllib.error.HTTPError as e:
        print(f"  [失败] GitHub API 返回 {e.code}: {e.read()[:500]!r}")
        raise
    except urllib.error.URLError as e:
        print(f"  [失败] 无法访问 GitHub API: {e.reason}")
        raise
    if not tags:
        return None
    return tags[0]["name"]


def download_file(url: str, dst: Path) -> None:
    """下载文件到目标路径，失败时打印清晰错误"""
    print(f"  [下载] {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "wows-zh-shipname-fixes"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp, open(dst, "wb") as f:
            shutil.copyfileobj(resp, f)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"下载失败 HTTP {e.code}: {url}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"下载失败: {e.reason}: {url}") from e


def fetch_mo(tag: str, out_dir: Path) -> dict[str, Path]:
    """用 raw URL 直接下载三个语言的 .mo 文件到 out_dir"""
    result = {}
    for lang in LANGS:
        rel = MO_PATH_TMPL.format(lang=lang)
        url = f"{RAW_BASE}/{urllib.parse.quote(tag)}/{rel}"
        dst = out_dir / lang / "global.mo"
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            download_file(url, dst)
            result[lang] = dst
            print(f"  [OK] {lang}: {dst} ({dst.stat().st_size:,} 字节)")
        except RuntimeError as e:
            print(f"  [警告] {e}")
    return result


# 舰船名词条键: IDS_P?S???? 或 IDS_P?S????_FULL (无其他后缀)
SHIP_KEY_RE = re.compile(r"^IDS_P[A-Z]S[A-Z]\d{3}(?:_FULL)?$")


def po_to_csv(po, csv_path: Path) -> None:
    """把 polib PO 对象导出为 csv (键值, 翻译)"""
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["键值(key)", "翻译(msgstr)"])
        for entry in po:
            if entry.msgid == "":
                continue  # 跳过文件头元数据条目
            if entry.msgid_plural and entry.msgstr_plural:
                # 复数条目: 翻译存在 msgstr_plural, 取第一个形式 (zh/zh_sg nplurals=1)
                msgstr = entry.msgstr_plural.get(0, "") or ""
            else:
                msgstr = entry.msgstr or ""
            w.writerow([entry.msgid, msgstr])


def extract_ship_csv(po, ship_path: Path) -> None:
    """从 po 中提取舰船名键 (IDS_P?S???? / IDS_P?S????_FULL) 到 ship.csv"""
    count = 0
    with open(ship_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["键值(key)", "翻译(msgstr)"])
        for entry in po:
            if SHIP_KEY_RE.match(entry.msgid or ""):
                w.writerow([entry.msgid, entry.msgstr])
                count += 1
    print(f"  [CSV] {ship_path.name}: 提取舰船名词条 {count} 条")


def ensure_csvs(version_dir: Path) -> None:
    """确保版本目录下三语言的 global.csv / ship.csv 齐全。

    早期同步的版本可能没有 CSV(导出功能后加), 从已有 global.po 补生成。
    若 po 也不存在则跳过(该语言可能下载失败)。
    """
    for lang in LANGS:
        po_path = version_dir / lang / "global.po"
        if not po_path.exists():
            continue
        g_csv = version_dir / lang / "global.csv"
        s_csv = version_dir / lang / "ship.csv"
        if g_csv.exists() and s_csv.exists():
            continue
        po = polib.pofile(str(po_path))
        if not g_csv.exists():
            po_to_csv(po, g_csv)
            print(f"  [补生成] {lang}/global.csv")
        if not s_csv.exists():
            extract_ship_csv(po, s_csv)
            print(f"  [补生成] {lang}/ship.csv")


def decompile(mo_path: Path, po_path: Path) -> polib.POFile:
    """修复文件头并用 polib 反编译 .mo -> .po

    注意: wgmods 的 mo 元数据换行符丢失, 必须先 fix_mo_header,
    否则 polib 无法解析 charset 会抛 UnicodeDecodeError。
    """
    data = mo_path.read_bytes()
    data = fix_mo_header(data)
    tmp_mo = mo_path.with_suffix(".fixed.mo")
    tmp_mo.write_bytes(data)
    try:
        po = polib.mofile(str(tmp_mo))
        po.save_as_pofile(str(po_path))
        print(f"  [反编译] {mo_path.name} -> {po_path.name} ({len(po)} 条)")
        return po
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
        # 已同步过的版本: 若 CSV 缺失(早期版本没有导出功能), 从 po 补生成
        ensure_csvs(out_dir)
        return 0

    print(f"拉取版本 {tag} 的翻译文件 ...")
    out_dir.mkdir(parents=True, exist_ok=True)
    mos = fetch_mo(tag, out_dir)
    if not mos:
        print("没有获取到任何 mo 文件，终止")
        return 1
    for lang, mo_path in mos.items():
        po = decompile(mo_path, mo_path.parent / "global.po")
        po_to_csv(po, mo_path.parent / "global.csv")
        extract_ship_csv(po, mo_path.parent / "ship.csv")

    (out_dir / "README.md").write_text(
        f"""# 版本 {tag}

ModSDK 翻译文件快照，来源: {REPO} 标签 `{tag}`。

## 目录内容

| 文件/目录 | 说明 |
|---|---|
| `zh/` `zh_sg/` `en/` | 各语言的原始 .mo、反编译 .po、全部词条 CSV 与舰船词条 CSV |
| `global.xlsx` | 三语言对照表（键值/zh/zh_sg/en/最终翻译），数据区中文微软雅黑/英文 Arial 字体 |
| `ship.xlsm` | 舰船词条表格（含 VB 宏自动配色，最终翻译列人工填写） |
| `global_diff.xlsx` | 与上一版本的全部词条差异（新旧翻译对比） |
| `ship_diff.xlsx` | 与上一版本的舰船词条差异（最终翻译列可填写） |

## 语言目录说明

每个语言目录（zh / zh_sg / en）包含：

- `global.mo` - 原始翻译文件（下载自 ModSDK）
- `global.po` - 反编译后的可读文本
- `global.csv` - 全部键值对（UTF-8 BOM，Excel 可直接打开）
- `ship.csv` - 舰船词条键值对（`IDS_P?S????` 与 `IDS_P?S????_FULL`）

## 翻译入口

- 在 `ship.xlsm` 的 **最终翻译** 列填写修正后的译名并保存
- 新版本生成时会按键值自动迁移旧版本的最终翻译，**新增舰船留空待填**
""",
        encoding="utf-8",
    )
    print(f"完成: 已保存到 {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
