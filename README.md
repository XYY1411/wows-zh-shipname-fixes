# wows-zh-shipname-fixes

修正《战舰世界》(World of Warships) 简体中文舰船名称翻译错误的勘误项目。

本仓库自动从 [wgmods/ModSDK](https://github.com/wgmods/ModSDK) 同步三种语言的
翻译文件（`.mo`），反编译为可读的 `.po`，按版本号归档保存，供人工校对与修正。

## 目录结构

```
wows-zh-shipname-fixes/
├── .github/workflows/
│   └── sync-translations.yml   # 自动同步工作流
├── scripts/
│   └── sync_translations.py    # 拉取 + 修复 + 反编译脚本
├── translations/               # 翻译快照（由 workflow 自动生成）
│   └── <版本号>/               # 例如 v1.0.0
│       ├── zh/global.mo        # 原始 .mo 文件
│       ├── zh/global.po        # 反编译产物
│       ├── zh-sg/global.mo
│       ├── zh-sg/global.po
│       ├── en/global.mo
│       └── en/global.po
└── README.md
```

## 自动同步工作流

- **触发方式**：每天 03:00 UTC（北京时间 11:00）自动检查一次；也可在
  Actions 页面手动点击 **Run workflow** 立即执行。
- **数据来源**：[wgmods/ModSDK](https://github.com/wgmods/ModSDK) 的
  `global.mo/{zh,zh-sg,en}/LC_MESSAGES/global.mo`（对应 tag）。
- **处理流程**：
  1. 查询 ModSDK 最新 tag，与本地已有版本比较；
  2. 若有新版本，用 sparse checkout 拉取三个语言的 `.mo` 文件；
  3. 修复 `.mo` 文件头（wgmods 的元数据丢失换行符、charset 声明混乱，
     需要重建元数据后才能被 gettext 解析）；
  4. 用 `polib` 反编译为 `.po`；
  5. 按版本号存入 `translations/<版本号>/`，**旧版本永远保留**；
  6. 自动提交并推送。
- **本地运行**：`python scripts/sync_translations.py`（需 `pip install polib`）。

## 翻译修正流程（人工）

1. 在 `translations/<版本号>/<语言>/global.po` 中查找有误的舰船名词条；
2. 修正 `msgstr`；
3. 需要生成补丁或 `.mo` 时，可用 `msgfmt`（gettext 工具）将 `.po`
   编译回 `.mo`。

## 相关

- 舰船名键格式：`IDS_P?S????`（第一个 `?` 为系别，第二个 `?` 为舰种）
- 配套 Excel 工作文件：`wows_翻译对照_舰船筛选版.xlsm`（含 VB 宏自动配色）
