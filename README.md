# wows-zh-shipname-fixes

修正《战舰世界》(World of Warships) 简体中文舰船名称翻译错误的勘误项目。

本仓库自动从 [wgmods/ModSDK](https://github.com/wgmods/ModSDK) 同步三种语言的
翻译文件（`.mo`），反编译为可读的 `.po`，导出 CSV 并生成 Excel 对照表与版本
差异表，按版本号归档保存，供人工校对与修正。

## 目录结构

```
wows-zh-shipname-fixes/
├── .github/workflows/
│   └── sync-translations.yml   # 自动同步 + 生成表格工作流
├── scripts/
│   ├── sync_translations.py    # 拉取 .mo + 修复文件头 + 反编译 + CSV 导出
│   └── generate_tables.py      # 由 CSV 生成 xlsx/xlsm 表格与版本差异
├── templates/
│   └── ship_template.xlsm      # ship.xlsm 的干净模板(含 VB 宏, 无数据)
├── translations/               # 翻译快照(按版本号)
│   └── <版本号>/               # 例如 15.7.0
│       ├── zh/                 # global.mo / global.po / global.csv / ship.csv
│       ├── zh_sg/              # 同上
│       ├── en/                 # 同上
│       ├── global.xlsx         # 三语言对照表(不着色, 数据区 Consolas)
│       ├── ship.xlsm           # 舰船词条 VB 表格(宏与模板一致)
│       ├── global_diff.xlsx    # 与上一版本的全部词条差异(仅新版本有)
│       └── ship_diff.xlsx      # 与上一版本的舰船词条差异(不对比最终翻译列)
└── README.md
```

## 自动同步工作流

- **触发方式**：每天 03:00 UTC（北京时间 11:00）自动检查一次；也可在
  Actions 页面手动点击 **Run workflow** 立即执行。
- **数据来源**：[wgmods/ModSDK](https://github.com/wgmods/ModSDK) 的
  `global.mo/{zh,zh_sg,en}/LC_MESSAGES/global.mo`（对应 tag，
  注意语言目录是 **zh_sg(下划线)**）。
- **处理流程**：
  1. 查询 ModSDK 最新 tag，与本地已有版本比较；
  2. 有新版本时，用 raw URL 直接下载三个语言的 `.mo` 文件；
  3. 修复 `.mo` 文件头（wgmods 元数据换行符丢失，需重建后才能解析）；
  4. 用 `polib` 反编译为 `.po`，导出 `global.csv`（全部词条）与
     `ship.csv`（`IDS_P?S????` 与 `IDS_P?S????_FULL` 舰船词条）；
  5. 已同步版本若 CSV 缺失会自动补生成；
  6. 自动生成表格（见下），按版本号存入 `translations/<版本号>/`，
     **旧版本永远保留**；
  7. 自动提交并推送。

## 表格生成（generate_tables.py）

```
python scripts/generate_tables.py            # 自动取最新两个版本
python scripts/generate_tables.py <新版本> <旧版本>
```

- `global.xlsx`：三语言对照（键值/zh/zh_sg/en/最终翻译），不着色；
- `ship.xlsm`：舰船词条表格，基于 `templates/ship_template.xlsm`
  生成，**VB 宏与布局完全一致**（E 列配色、BCD 三列关系配色、A 列系别×舰种配色）；
- `global_diff.xlsx`：新版本相对上一版本的全部差异（新增/删除/修改，
  新旧翻译并排对比）；
- `ship_diff.xlsx`：仅舰船词条的差异，**不对比最终翻译列**；
- 数据区使用系统自带 **Consolas** 等宽字体，打开文件无需安装任何字体；
- 生成后自动清理幽灵空行（保证 `max_row` 与实际数据一致）。

## 翻译修正流程（人工）

1. 在 `translations/<版本号>/<语言>/global.csv` 中查找有误的舰船名词条；
2. 修正 `msgstr`；
3. 需要生成补丁或 `.mo` 时，可用 `msgfmt`（gettext 工具）将 `.po`
   编译回 `.mo`。

## 相关

- 舰船名键格式：`IDS_P?S????`（第一个 `?` 为系别，第二个 `?` 为舰种）
- 配套本地工作文件：`wows_翻译对照_舰船筛选版.xlsm`（含 VB 宏自动配色）
