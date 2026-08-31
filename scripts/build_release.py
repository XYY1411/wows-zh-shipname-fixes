#!/usr/bin/env python3
"""生成 mod 发布文件: 翻译后的 global.mo

流程:
    1. 翻译后的 ship.xlsm -> ship.csv (存放到 ship.xlsm 相同目录)
    2. zh_sg/global.csv + ship.csv 合并 (ship 键值替换同名键) -> release/<版本>/global.csv
    3. global.csv -> global.po (存放到发布目录)
    4. global.po -> global.mo, 复制到 zh 与 zh_sg 的 LC_MESSAGES/

用法:
    python scripts/build_release.py            # 默认最新版本
    python scripts/build_release.py 15.7.0     # 指定版本
"""
import array
import csv
import re
import shutil
import struct
import sys
from datetime import datetime
from pathlib import Path

import polib
from openpyxl import load_workbook

# CSV 表头(与 sync_translations.py 导出的格式一致)
CSV_HEADER = ["键值(key)", "翻译(msgstr)"]
RELEASE_DIR_NAME = "release"  # 发布文件夹名(仓库根目录下)


def next_release_dir(repo: Path, version: str) -> Path:
    """正式发布: 找 <version>-r<n> 中最大的 n, 返回下一个版本目录 <version>-r(n+1)"""
    base = repo / RELEASE_DIR_NAME
    pattern = re.compile(rf"^{re.escape(version)}-r(\d+)$")
    max_n = 0
    if base.exists():
        for d in base.iterdir():
            if d.is_dir():
                m = pattern.match(d.name)
                if m:
                    max_n = max(max_n, int(m.group(1)))
    n = max_n + 1
    return base / f"{version}-r{n}"


def write_version_txt(release_dir: Path, version: str, mod_version: str, variant: str = "") -> None:
    """写 mod 版本元数据文件"""
    if variant == "full":
        type_label = "全名版(缩写键也用完整船名)"
    else:
        type_label = "标准版(缩写键)"
    lines = [
        f"mod版本:      {mod_version}",
        f"对应游戏版本:  {version}",
        f"版本类型:      {type_label}",
        f"构建时间:      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]
    (release_dir / "version.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  [版本] {release_dir.name}/version.txt (mod {mod_version})")


def find_latest_version(repo: Path) -> str:
    """从 translations/ 找出最大的版本号"""
    versions = []
    for d in (repo / "translations").iterdir():
        if not d.is_dir():
            continue
        parts = d.name.split(".")
        if len(parts) == 3:
            try:
                versions.append((tuple(int(x) for x in parts), d.name))
            except ValueError:
                pass
    if not versions:
        raise SystemExit("translations/ 下没有版本目录")
    versions.sort()
    return versions[-1][1]


def ship_xlsm_to_csv(ship_xlsm: Path, out_csv: Path) -> int:
    """翻译后的 ship.xlsm -> ship.csv (键值, 最终翻译)"""
    wb = load_workbook(ship_xlsm, read_only=True, data_only=True)
    ws = wb.active
    rows = []
    for row in ws.iter_rows(min_row=2, max_col=5, values_only=True):
        key = row[0]
        if key:
            rows.append([str(key), str(row[4] or "")])
    wb.close()
    with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(CSV_HEADER)
        w.writerows(rows)
    print(f"  [生成] {out_csv} ({len(rows)} 条)")
    return len(rows)


# 无后缀舰船键: IDS_P?S???? (不带 _FULL); 对应 _FULL 键为其完整名称
SHIP_BASE_KEY_RE = re.compile(r"^IDS_P[A-Z]S[A-Z]\d{3}$")


def merge_global_csv(base_csv: Path, ship_csv: Path, out_csv: Path, full_mode: bool = False) -> int:
    """用 ship.csv 替换 base_csv 中键名相同的键值, 其余原样保留。
    full_mode: 把无后缀键 IDS_P?S???? 的翻译替换为对应 _FULL 键的翻译(全名版)。
    """
    # 读出 ship.csv 全部 (键, 最终翻译)
    ship_map = {}
    with open(ship_csv, encoding="utf-8-sig", newline="") as f:
        for row in csv.reader(f):
            if row and row[0] and row[0] != CSV_HEADER[0]:
                ship_map[row[0]] = row[1] if len(row) > 1 else ""

    replace = dict(ship_map)
    if full_mode:
        # 无后缀键: 改用对应 _FULL 键的翻译, 让缩写键位置也显示完整船名
        for k in list(replace):
            if SHIP_BASE_KEY_RE.match(k):
                full_k = k + "_FULL"
                if full_k in ship_map:
                    replace[k] = ship_map[full_k]

    with open(base_csv, encoding="utf-8-sig", newline="") as f:
        reader = list(csv.reader(f))

    changed = 0
    body = []
    for row in reader[1:]:
        if row and row[0] in replace and replace[row[0]] != (row[1] if len(row) > 1 else ""):
            changed += 1
        if row:
            if len(row) < 2:
                row.append("")
            if row[0] in replace:
                row[1] = replace[row[0]]
        body.append(row)

    with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(CSV_HEADER)
        w.writerows(body)
    print(f"  [生成] {out_csv} ({len(body)} 条, 替换翻译 {changed} 条)")
    return changed


def csv_to_po(csv_path: Path, po_path: Path) -> int:
    """global.csv -> global.po"""
    po = polib.POFile()
    po.metadata = {
        "Project-Id-Version": "wows-zh-shipname-fixes",
        "Report-Msgid-Bugs-To": "",
        "POT-Creation-Date": "",
        "PO-Revision-Date": "",
        "Last-Translator": "XYY1411",
        "Language-Team": "简体中文",
        "Language": "zh_CN",
        "MIME-Version": "1.0",
        "Content-Type": "text/plain; charset=UTF-8",
        "Content-Transfer-Encoding": "8bit",
        "Plural-Forms": "nplurals=1; plural=0;",
    }
    count = 0
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        for row in csv.reader(f):
            if not row or not row[0] or row[0] == CSV_HEADER[0]:
                continue
            msgid, msgstr = row[0], row[1] if len(row) > 1 else ""
            po.append(polib.POEntry(msgid=msgid, msgstr=msgstr))
            count += 1
    po.save(str(po_path))
    print(f"  [生成] {po_path} ({count} 条)")
    return count


def po_to_mo(po_path: Path, mo_path: Path) -> None:
    """global.po -> global.mo (保留所有键, 含空翻译键, 避免游戏显示键值)

    说明: polib 的 save_as_mofile 用 translated_entries() 只编译已翻译条目,
    会丢掉空翻译键, 导致游戏显示键值(IDS_XXX)。这里参考 polib to_binary
    的实现, 但遍历全部条目, 保证 mod mo 的键集合与官方 mo 完全一致。
    同时复数条目(msgid_plural)也按 gettext 规范写入(\x00 分隔)。
    """
    po = polib.pofile(str(po_path))
    # 参考 polib to_binary, 但用全部条目(空翻译键也写入, 与官方 mo 键集合一致)
    offsets = []
    entries = list(po)
    entries.sort(key=lambda o: o.msgid_with_context.encode("utf-8"))
    entries = [po.metadata_as_entry()] + entries
    entries_len = len(entries)
    ids, strs = b"", b""
    for e in entries:
        msgid = b""
        if e.msgctxt:
            msgid = po._encode(e.msgctxt + "\4")
        if e.msgid_plural:
            msgstr = []
            for index in sorted(e.msgstr_plural.keys()):
                msgstr.append(e.msgstr_plural[index])
            msgid += po._encode(e.msgid + "\0" + e.msgid_plural)
            msgstr = po._encode("\0".join(msgstr))
        else:
            msgid += po._encode(e.msgid)
            msgstr = po._encode(e.msgstr)
        offsets.append((len(ids), len(msgid), len(strs), len(msgstr)))
        ids += msgid + b"\0"
        strs += msgstr + b"\0"
    keystart = 7 * 4 + 16 * entries_len
    valuestart = keystart + len(ids)
    koffsets, voffsets = [], []
    for o1, l1, o2, l2 in offsets:
        koffsets += [l1, o1 + keystart]
        voffsets += [l2, o2 + valuestart]
    offsets = koffsets + voffsets
    output = struct.pack(
        "Iiiiiii",
        0x950412DE,  # gettext magic
        0, entries_len, 7 * 4, 7 * 4 + entries_len * 8, 0, keystart
    )
    output += array.array("i", offsets).tobytes()
    output += ids
    output += strs
    mo_path.write_bytes(output)
    print(f"  [生成] {mo_path} ({entries_len - 1} 条, 含空翻译键)")


def main():
    repo = Path(__file__).resolve().parent.parent
    args = [a for a in sys.argv[1:] if a != "--release"]
    release_mode = "--release" in sys.argv   # 正式发布: 递增修订号, 不覆盖
    version = args[0] if args else find_latest_version(repo)
    print(f"构建 mod 发布版本: {version}")

    # 目标目录: 正式发布(递增 r<n>) 或 本地调试(覆盖最新)
    if release_mode:
        release_dir = next_release_dir(repo, version)
        mod_version = release_dir.name
        print(f"[正式发布] 生成新版本目录 {release_dir.name} (历史版本保留, 不覆盖)")
    else:
        release_dir = repo / RELEASE_DIR_NAME / version
        mod_version = version
        print(f"[本地调试] 覆盖最新目录 {release_dir.name} (不保留历史)")

    ver_dir = repo / "translations" / version
    if not ver_dir.exists():
        raise SystemExit(f"版本目录不存在: {ver_dir}")
    ship_xlsm = ver_dir / "ship.xlsm"
    if not ship_xlsm.exists():
        raise SystemExit(f"ship.xlsm 不存在: {ship_xlsm}")
    base_global = ver_dir / "zh_sg" / "global.csv"
    if not base_global.exists():
        raise SystemExit(f"zh_sg/global.csv 不存在: {base_global}")

    # 1. ship.xlsm -> ship.csv (与 ship.xlsm 同目录)
    print("1. 导出翻译后的 ship.csv ...")
    ship_csv = ver_dir / "ship.csv"
    ship_xlsm_to_csv(ship_xlsm, ship_csv)

    # 2. 构建两个子版本: standard(缩写) 与 _full(全名, 缩写键也用完整船名)
    release_dir.mkdir(parents=True, exist_ok=True)
    for variant in ("standard", "full"):
        variant_dir = release_dir / variant
        variant_dir.mkdir(parents=True, exist_ok=True)
        full_mode = (variant == "full")
        print(f"2. 合并生成 {variant}/global.csv ...")
        merged_csv = variant_dir / "global.csv"
        merge_global_csv(base_global, ship_csv, merged_csv, full_mode=full_mode)

        print(f"3. 生成 {variant}/global.po ...")
        po_path = variant_dir / "global.po"
        csv_to_po(merged_csv, po_path)

        print(f"4. 编译 {variant}/global.mo ...")
        mo_tmp = variant_dir / "global.mo"
        po_to_mo(po_path, mo_tmp)
        for lang in ("zh", "zh_sg"):
            target = variant_dir / lang / "LC_MESSAGES" / "global.mo"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(mo_tmp, target)
            print(f"  [发布] {target}")

        mod_variant = mod_version if variant == "standard" else f"{mod_version}-full"
        write_version_txt(variant_dir, version, mod_variant, variant)

    print(f"\n完成! 发布文件位于: {release_dir}/standard 与 {release_dir}/full")


if __name__ == "__main__":
    sys.exit(main())
