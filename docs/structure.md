# 目录结构与文件说明

```
wows-zh-shipname-fixes/
├── .github/workflows/
│   └── sync-translations.yml   # 自动同步 + 生成表格工作流
├── scripts/
│   ├── sync_translations.py    # 拉取 .mo + 修复文件头 + 反编译 + CSV 导出 + 版本 README
│   └── generate_tables.py      # 由 CSV 生成 xlsx/xlsm 表格、版本差异与翻译迁移
├── templates/
│   └── ship_template.xlsm      # ship.xlsm 的干净模板（含 VB 宏，无数据，字体已净化）
├── translations/               # 翻译快照（按版本号归档，旧版本永远保留）
│   └── <版本号>/               # 例如 15.7.0
│       ├── README.md           # 版本说明（自动生成）
│       ├── zh/ zh_sg/ en/      # 三种语言各一份：
│       │   ├── global.mo       #   原始翻译文件（下载自 ModSDK）
│       │   ├── global.po       #   反编译后的可读文本
│       │   ├── global.csv      #   全部键值对（UTF-8 BOM）
│       │   └── ship.csv        #   舰船词条键值对（IDS_P?S???? 与 _FULL）
│       ├── global.xlsx         # 三语言对照表（键值/zh/zh_sg/en/最终翻译）
│       ├── ship.xlsm           # 舰船词条表格（VB 宏自动配色，最终翻译列人工填写）
│       ├── global_diff.xlsx    # 与上一版本的全部词条差异（仅最新版本有）
│       └── ship_diff.xlsx      # 与上一版本的舰船词条差异（最终翻译列留空）
└── docs/                       # 本文档
```

## 数据流

```
ModSDK 官方 .mo
    ↓ sync_translations.py（拉取 → 修复文件头 → polib 反编译）
global.po / global.csv / ship.csv
    ↓ generate_tables.py（合并三语言 → 生成表格 → 计算差异 → 迁移翻译）
global.xlsx / ship.xlsm / global_diff.xlsx / ship_diff.xlsx
```

**CSV 是唯一数据源**，Excel 表格只是展示层——删掉 xlsx/xlsm 后重新运行脚本即可从 CSV 原样生成。

## 键值格式

- 舰船词条：`IDS_P?S????`（第一个 `?` 为系别，第二个 `?` 为舰种）及 `IDS_P?S????_FULL`
- 系别：A/B/F/G/H/I/J/R/U/V/W/X/Z（15 个）
- 舰种：A/B/C/D/S/X（6 个）
