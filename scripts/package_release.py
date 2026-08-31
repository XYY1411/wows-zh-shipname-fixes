#!/usr/bin/env python3
"""把 release/ 下某版本的 mod 发布文件打包为 4 种组合的 zip:

  [全量 global.mo | 增量 wowsZhShipnameFixes.mo] × [standard(缩写) | full(全名)]

输出到 dist/:
  <版本>-global-standard.zip   # 完整版, 缩写键
  <版本>-global-full.zip       # 完整版, 全名版
  <版本>-inc-standard.zip      # 增量版, 缩写键
  <版本>-inc-full.zip          # 增量版, 全名版

zip 内部: res_mods/texts/<zh|zh_sg>/LC_MESSAGES/<mo 文件名>

版本号支持 -r<n> 标记, 如 15.7.0-r1。

用法:
    python scripts/package_release.py              # 打包 release/ 下最新版本
    python scripts/package_release.py 15.7.0       # 打包指定版本
    python scripts/package_release.py 15.7.0-r1    # 打包带 -r 标记的版本
"""
import re
import sys
import zipfile
from pathlib import Path

RELEASE_DIR_NAME = "release"
OUT_DIR_NAME = "dist"
MOD_NAME = "wowsZhShipnameFixes"
VERSION_RE = re.compile(r"^(\d+\.\d+\.\d+)(?:-r(\d+))?$")
LANGS = ("zh", "zh_sg")
# 4 种组合: (kind, variant, mo 文件名)。kind: global=全量 / inc=增量
COMBOS = [
    ("global", "standard", "global.mo"),
    ("global", "full", "global.mo"),
    ("inc", "standard", f"{MOD_NAME}.mo"),
    ("inc", "full", f"{MOD_NAME}.mo"),
]


def find_latest_release_dir(repo: Path) -> Path:
    """从 release/ 找版本号最大(含 -r 修订)的目录"""
    base = repo / RELEASE_DIR_NAME
    candidates = []
    if not base.exists():
        raise SystemExit(f"{base} 目录不存在")
    for d in base.iterdir():
        if not d.is_dir():
            continue
        m = VERSION_RE.match(d.name)
        if m:
            parts = tuple(int(x) for x in m.group(1).split("."))
            rev = int(m.group(2) or 0)
            candidates.append((parts, rev, d))
    if not candidates:
        raise SystemExit(f"{base} 下没有版本目录")
    candidates.sort(key=lambda x: (x[0], x[1]))
    return candidates[-1][2]


def resolve_release_dir(repo: Path, version: str | None) -> Path:
    if version:
        d = repo / RELEASE_DIR_NAME / version
        if not d.exists():
            raise SystemExit(f"版本目录不存在: {d}")
        return d
    return find_latest_release_dir(repo)


def package_combo(release_dir: Path, out_dir: Path, kind: str, variant: str, mo_name: str):
    """打包一种组合为 zip: <版本>-<kind>-<variant>.zip(内部 res_mods/texts/<lang>/LC_MESSAGES/<mo>)"""
    src = release_dir / variant
    if not src.exists():
        print(f"  [跳过] {variant} 不存在")
        return None
    zip_path = out_dir / f"{release_dir.name}-{kind}-{variant}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for lang in LANGS:
            mo = src / lang / "LC_MESSAGES" / mo_name
            if mo.exists():
                z.write(mo, Path("res_mods/texts") / lang / "LC_MESSAGES" / mo_name)
    print(f"  [打包] {zip_path}")
    return zip_path


def main():
    repo = Path(__file__).resolve().parent.parent
    version = None
    if len(sys.argv) > 1 and sys.argv[1].strip():
        version = sys.argv[1]
    release_dir = resolve_release_dir(repo, version)
    out_dir = repo / OUT_DIR_NAME
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"打包版本: {release_dir.name} (全量/增量 × 缩写/full)")
    made = []
    for kind, variant, mo_name in COMBOS:
        zp = package_combo(release_dir, out_dir, kind, variant, mo_name)
        if zp:
            made.append(zp.name)
    if not made:
        print("没有可打包的组合")
        return 1
    print(f"完成! 共 {len(made)} 个 zip: {', '.join(made)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
