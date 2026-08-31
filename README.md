# wows-zh-shipname-fixes

《战舰世界》(World of Warships) 简体中文舰船译名勘误项目。从 [wgmods/ModSDK](https://github.com/wgmods/ModSDK) 同步官方翻译，供人工校对修正。发布提供 **标准版（缩写键）** 与 **全名版（`_FULL`）** 两种 mod。

## 做什么

- **自动同步**：每天检查 ModSDK 新版本，拉取 zh / zh_sg / en 翻译，按版本归档
- **生成表格**：`global.xlsx` 对照表、`ship.xlsm` 舰船词条（含 VB 宏配色）
- **版本差异 + 翻译迁移**：自动对比上一版本、迁移已填最终翻译
- **构建发布**：`build_release.py` 生成**仅含差异**的 `standard` / `full` 增量（按 zh/zh_sg 双语言），供 Localization Loader 加载；`--release` 递增修订号
- **打包发布**：`package_release.py` / 手动工作流打包为 `res_mods/texts` zip 并发布

## 去哪找文件

| 内容                   | 位置                                                                |
| ---------------------- | ------------------------------------------------------------------- |
| 翻译与表格             | `translations/<版本号>/`                                            |
| 三语言对照表           | `translations/<版本号>/global.xlsx`                                 |
| 舰船词条表（翻译入口） | `translations/<版本号>/ship.xlsm`                                   |
| 版本差异表             | `translations/<版本号>/global_diff.xlsx`、`ship_diff.xlsx`          |
| 原始键值数据           | `translations/<版本号>/<语言>/global.csv`、`ship.csv`               |
| mod 发布文件           | `release/<版本号>/{standard,full}/{zh,zh_sg}/LC_MESSAGES/{global.mo, wowsZhShipnameFixes.mo}` |
| 打包产物               | `dist/<版本号>-<variant>.zip`                                       |
| 同步工作流             | `.github/workflows/sync-translations.yml`                           |
| 打包工作流             | `.github/workflows/package-release.yml`                             |
| 生成脚本               | `scripts/sync_translations.py`、`generate_tables.py`                |
| 发布脚本               | `scripts/build_release.py`、`package_release.py`                    |

## 怎么用

- **看/填翻译**：打开 `translations/<版本号>/ship.xlsm`，在「最终翻译」列填写译名
- **构建发布**：`py -3 scripts/build_release.py [版本号]`（生成**完整版 global.mo** + **增量版**）；正式发布加 `--release`
- **打包**：`py -3 scripts/package_release.py [版本号]`（4 种组合：global/inc × standard/full）
- **发布**：GitHub Actions 手动运行 _打包并发布 Mod_

## 文档

- [目录结构](docs/structure.md)
- [工作流](docs/workflow.md)
- [表格与差异](docs/tables.md)
- [翻译流程](docs/translation.md)
- [发布构建](docs/release.md)

## 感谢 · 许可

- 感谢 & 参考
  - [战舰世界全系舰名翻译勘误](https://www.bilibili.com/opus/1234142123653070865) by Mrtn
  - [战舰世界国服与外服舰名差异锐评](https://www.bilibili.com/opus/1152524855843749906) by Mrtn
  - [维基百科](https://www.wikipedia.org/)
  - 译名室, 新华通讯社. 世界人名翻译大辞典（第二版）[M]. 北京: 中国对外翻译出版公司, 2007. ISBN 9787500107996. OCLC 163575075
  - 周定国. 世界地名翻译大辞典[M]. 北京: 中国对外翻译出版公司, 2008. ISBN 9787500107538
- 翻译数据源自 [wgmods/ModSDK](https://github.com/wgmods/ModSDK)，版权归 © 2012–2026 Wargaming.net，仅作非商业勘误
- 本项目修正翻译/脚本/文档采用 CC BY-NC-SA 4.0；与 Wargaming.net 无官方关联
- 详见 [LICENSE](LICENSE)
