# wows-zh-shipname-fixes

修正《战舰世界》(World of Warships) 简体中文舰船名称翻译错误的勘误项目。

自动从 [wgmods/ModSDK](https://github.com/wgmods/ModSDK) 同步官方翻译，生成三语言对照表与版本差异表，供人工校对并修正舰船译名。

## 项目做什么

1. **自动同步** — GitHub Actions 每天检查 ModSDK 新版本，拉取 zh / zh_sg / en 三种语言的翻译文件，按版本号归档（旧版本保留）
2. **生成表格** — 每个版本自动生成 CSV、三语言对照表 `global.xlsx`、舰船词条表 `ship.xlsm`（含 VB 宏自动配色）
3. **版本差异** — 新版本自动对比上一版本，生成差异表 `global_diff.xlsx` / `ship_diff.xlsx`
4. **翻译迁移** — 生成新版本时按键值自动迁移旧版本已填写的最终翻译，只留新增舰船待填

## 去哪找文件

| 内容 | 位置 |
|---|---|
| 各版本翻译与表格 | `translations/<版本号>/`（如 `translations/15.7.0/`） |
| 三语言对照表 | `translations/<版本号>/global.xlsx` |
| 舰船词条表（翻译入口） | `translations/<版本号>/ship.xlsm` |
| 版本差异表 | `translations/<版本号>/global_diff.xlsx`、`ship_diff.xlsx` |
| 原始键值数据 | `translations/<版本号>/<语言>/global.csv`、`ship.csv` |
| 自动同步工作流 | `.github/workflows/sync-translations.yml` |
| 生成脚本 | `scripts/sync_translations.py`、`scripts/generate_tables.py` |

## 怎么用

- **看翻译**：打开 `translations/<版本号>/global.xlsx`（全部词条）或 `ship.xlsm`（舰船词条，打开后启用宏自动配色）
- **填翻译**：在 `ship.xlsm` 的 **最终翻译** 列填写修正译名，保存提交
- **触发同步**：到 GitHub Actions 页面手动 Run workflow，或等每天 03:00 UTC 自动执行

## 详细文档

- [目录结构与文件说明](docs/structure.md)
- [自动同步工作流](docs/workflow.md)
- [表格与差异生成](docs/tables.md)
- [翻译修正流程](docs/translation.md)
