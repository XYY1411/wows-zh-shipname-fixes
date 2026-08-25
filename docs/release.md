# mod 发布构建

脚本：`scripts/build_release.py`

```
py -3 scripts/build_release.py            # 默认最新版本
py -3 scripts/build_release.py 15.7.0     # 指定版本
```

## 发布目录结构

```
release/<版本号>/
├── global.csv          # 合并后的完整键值（舰船键已替换为最终翻译）
├── global.po           # 中间产物（供检查/再编译）
├── global.mo           # 编译产物
├── zh/LC_MESSAGES/global.mo     # mod 发布文件（放入游戏 zh 目录）
└── zh_sg/LC_MESSAGES/global.mo  # mod 发布文件（放入游戏 zh_sg 目录）
```

玩家拿到 `zh/LC_MESSAGES/global.mo`（或 `zh_sg/` 版本），放入游戏
`bin/<版本>/res_mods/texts/<语言>/LC_MESSAGES/` 即可生效。

## 构建流程

```
① 翻译后的 ship.xlsm ──→ translations/<版本号>/ship.csv   （导出最终翻译 E 列）
② zh_sg/global.csv + ship.csv ──→ release/<版本号>/global.csv
    （舰船键用最终翻译替换同名键值，其余原样保留）
③ global.csv ──→ global.po
④ global.po ──→ global.mo，复制到 zh / zh_sg 的 LC_MESSAGES/
```

## 关键设计

1. **键集合与官方完全一致**：编译 mo 时不使用 `polib.save_as_mofile`
   （其 `translated_entries()` 会丢弃空翻译键，导致游戏显示键值 `IDS_XXX`），
   而是自定义编译器遍历全部条目——包括空翻译键与复数条目。
2. **复数条目**（`msgid_plural`）：按 gettext 规范用 NUL 字节连接多个形式写入。
3. **替换统计**：输出中的"替换翻译 N 条"指最终翻译与官方 zh_sg **不同**的舰船键数，
   其余与官方一致的原样保留。

## 环境要求

- Python 3.8+，依赖 `openpyxl`、`polib`
- 统一用 `py -3` 运行（Windows 多 Python 环境下依赖装在 py 默认解释器上）

## 与表格生成的关系

`build_release.py` 独立于 `generate_tables.py`：
- 表格生成是**自动**的（workflow），发布构建是**人工**执行的（翻译完成后）
- 发布构建读取 `ship.xlsm` 的最终翻译 + `zh_sg/global.csv`，不修改表格
- 发布文件在 `release/`，与 `translations/` 的表格互不影响
