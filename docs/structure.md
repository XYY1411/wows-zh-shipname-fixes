# 目录结构与文件说明

```
wows-zh-shipname-fixes/
├── .github/workflows/
│   ├── sync-translations.yml   # 自动同步 + 生成表格
│   └── package-release.yml     # 打包 standard/full 为 zip 并发布
├── scripts/
│   ├── sync_translations.py    # 同步 ModSDK 翻译(.mo→po→csv)
│   ├── generate_tables.py      # 生成 xlsx/xlsm 表格与差异
│   ├── build_release.py        # 生成完整+增量 standard/full 发布
│   └── package_release.py      # 打包为 res_mods/texts zip
├── templates/
│   └── ship_template.xlsm      # ship.xlsm 模板(含 VB 宏)
├── translations/<版本号>/      # 翻译快照(旧版本保留)
│   ├── README.md  ship.csv
│   ├── zh/ zh_sg/ en/          # global.mo /.po /.csv + ship.csv
│   ├── global.xlsx  ship.xlsm
│   └── global_diff.xlsx  ship_diff.xlsx
├── release/<版本号>[/-r<n>]/
│   ├── standard/               # 标准版(缩写键)
│   │   ├── zh/LC_MESSAGES/global.mo            # 完整版(无 loader 用)
│   │   ├── zh/LC_MESSAGES/wowsZhShipnameFixes.mo   # 增量版(loader 用)
│   │   ├── zh_sg/LC_MESSAGES/global.mo         # 完整版(国际服)
│   │   ├── zh_sg/LC_MESSAGES/wowsZhShipnameFixes.mo  # 增量版(国际服)
│   │   └── version.txt
│   └── full/                   # 全名版(缩写键用 _FULL, 结构同 standard)
├── dist/                       # 打包产物(<版本号>-<variant>.zip, 不提交)
├── tmp/                        # 本地临时(不提交)
└── docs/                       # 文档
```

## 数据流

```
ModSDK .mo → sync_translations.py → global.po/csv + ship.csv
    → generate_tables.py → global.xlsx / ship.xlsm / *_diff.xlsx
    → build_release.py → release/<版本号>/{standard,full}/{zh,zh_sg}/LC_MESSAGES/{global.mo, wowsZhShipnameFixes.mo}
    → package_release.py → dist/<版本号>-{standard,full}.zip (res_mods/texts/...)
```

CSV 是唯一数据源，表格可由 CSV 重新生成。

## 键值格式

- 舰船词条：`IDS_P?S????`、`IDS_P?S????_FULL`
- 系别：A/B/F/G/H/I/J/R/U/V/W/X/Z；舰种：A/B/C/D/S/X
