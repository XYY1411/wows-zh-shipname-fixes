# mod 发布构建

`scripts/build_release.py` 生成 **standard（缩写键）** 与 **full（全名版）** 两个子版本；`scripts/package_release.py` 打包。

## 构建

```
py -3 scripts/build_release.py [版本号]         # 默认最新; 本地调试(覆盖)
py -3 scripts/build_release.py 15.7.0 --release # 正式发布: 递增修订号 -r<n>, 不覆盖
```

## 结构

```
release/<版本号>[/-r<n>]/
├── standard/   global.csv/.po/.mo  zh/LC_MESSAGES/global.mo  zh_sg/...  version.txt
└── full/       结构同 standard, 但缩写键用 _FULL 的完整船名
```

玩家取 `standard/`（或 `full/`）的 `zh/`（或 `zh_sg/`）`global.mo`，放入 `bin/<版本>/res_mods/texts/<语言>/LC_MESSAGES/`。

## 流程

`ship.xlsm` → `ship.csv` → 合成 `{standard,full}/global.csv`（standard 用最终翻译替换；full 再把缩写键 `IDS_P?S????` 替换为对应 `_FULL` 值）→ po → mo → 复制到 zh/zh_sg → `version.txt`。

## 打包

```
py -3 scripts/package_release.py [版本号(-r)]
```

输出 `dist/<版本号>-standard.zip` / `-full.zip`，内部 `res_mods/texts/<zh|zh_sg>/LC_MESSAGES/global.mo`；或用手动工作流发布为 Release。

## 关键点

- 编译 mo 不用 polib `save_as_mofile`（会丢空翻译键），而是自定义编译器遍历全部条目（含复数条目）
- `full` 版只处理无后缀键 `IDS_P?S????`，有对应 `_FULL` 则替换为其值，无则保持原值
- 每个发布目录含 `version.txt`（mod版本/游戏版本/类型/构建时间）
