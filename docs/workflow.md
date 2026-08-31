# 工作流

## 自动同步（sync-translations.yml）

每天 03:00 UTC（北京时间 11:00）或手动触发。流程：

1. 安装依赖 `polib`、`openpyxl`
2. `sync_translations.py`：查 ModSDK 最新 tag，有新版本则下载三个语言的 `.mo`，修复文件头并反编译为 `.po`，导出 `global.csv`、`ship.csv`；旧版本缺 CSV 时补生成
3. `generate_tables.py`：按最新两个版本生成 `global.xlsx`/`ship.xlsm`/差异表，并迁移旧版最终翻译
4. 提交推送：**只认 `.mo/.po/.csv` 是否有变化**（`xlsx/xlsm` 每次生成含时间戳、字节会变，不能当变更依据）；有实质变化才提交

## 打包发布（package-release.yml，手动）

输入可选 `version`（留空取最新，可带 `-r` 如 `15.7.0-r1`）。流程：

1. checkout（`release/` 已在仓库）
2. `package_release.py [version]` 打包 `standard`/`full` 到 `dist/`
3. 确定版本号（输入值或 `ls release | sort -V | tail -1`）
4. 上传 `dist/*.zip` 到 GitHub Release（tag=版本号）
