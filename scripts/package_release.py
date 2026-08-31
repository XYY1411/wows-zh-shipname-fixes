#!/usr/bin/env python3
"""把 release/ 下某版本的 standard 与 full 的 zh/zh_sg 打包为 mod zip。

输出到 dist/:
    dist/<版本>-standard.zip   (内部结构 res_mods/texts/zh, res_mods/texts/zh_sg)
    dist/<版本>-full.zip

版本号支持 -r<n> 标记, 如 15.7.0-r1, 打包为 15.7.0-r1-standard.zip。

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
VERSION_RE = re.compile(r"^(\d+\.\d+\.\d+)(?:-r(\d+))?$")
LANGS = ("zh", "zh_sg")
VARIANTS = ("standard", "full")


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


def package_variant(release_dir: Path, variant: str, out_dir: Path):
    """把 <release_dir>/<variant> 的 zh + zh_sg 打包为 res_mods/texts/ 结构的 zip"""
    src = release_dir / variant
    if not src.exists():
        print(f"  [跳过] {variant} 不存在")
        return None
    zip_path = out_dir / f"{release_dir.name}-{variant}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for lang in LANGS:
            lang_dir = src / lang
            if not lang_dir.exists():
                continue
            for p in sorted(lang_dir.rglob("*")):
                if p.is_file():
                    # zip 根 = res_mods/texts/<lang>/...
                    z.write(p, Path("res_mods/texts") / lang / p.relative_to(lang_dir))
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

    print(f"打包版本: {release_dir.name}")
    made = []
    for variant in VARIANTS:
        zp = package_variant(release_dir, variant, out_dir)
        if zp:
            made.append(zp.name)
    if not made:
        print("没有可打包的版本")
        return 1
    print(f"完成! 共 {len(made)} 个 zip: {', '.join(made)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
