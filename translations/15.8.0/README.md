# 版本 15.8.0

ModSDK 翻译文件快照，来源: wgmods/ModSDK 标签 `15.8.0`。

## 目录内容

| 文件/目录 | 说明 |
|---|---|
| `zh/` `zh_sg/` `en/` | 各语言的原始 .mo、反编译 .po、全部词条 CSV 与舰船词条 CSV |
| `global.xlsx` | 三语言对照表（键值/zh/zh_sg/en/最终翻译），数据区中文微软雅黑/英文 Arial 字体 |
| `ship.xlsm` | 舰船词条表格（含 VB 宏自动配色，最终翻译列人工填写） |
| `global_diff.xlsx` | 与上一版本的全部词条差异（新旧翻译对比） |
| `ship_diff.xlsx` | 与上一版本的舰船词条差异（最终翻译列可填写） |

## 语言目录说明

每个语言目录（zh / zh_sg / en）包含：

- `global.mo` - 原始翻译文件（下载自 ModSDK）
- `global.po` - 反编译后的可读文本
- `global.csv` - 全部键值对（UTF-8 BOM，Excel 可直接打开）
- `ship.csv` - 舰船词条键值对（`IDS_P?S????` 与 `IDS_P?S????_FULL`）

## 翻译入口

- 在 `ship.xlsm` 的 **最终翻译** 列填写修正后的译名并保存
- 新版本生成时会按键值自动迁移旧版本的最终翻译，**新增舰船留空待填**
