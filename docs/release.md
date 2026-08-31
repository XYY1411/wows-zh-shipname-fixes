# mod 发布构建

`scripts/build_release.py` 为每个版本（standard / full）同时输出**完整版**与**增量版**，按 zh（国服简中）/ zh_sg（国际服简中）分别提供：

- **完整版 `global.mo`**：键集合与官方一致（含空翻译键），适合**未安装 Localization Loader** 的玩家（传统全量覆盖）
- **增量版 `wowsZhShipnameFixes.mo`**：只含「最终翻译 ≠ 官方」的舰船键，带 `X-LocalizationLoader-Priority` 头，适合**使用阿斯兰 / Localization Loader** 的玩家

`scripts/package_release.py` 负责打包。

## 构建

```
py -3 scripts/build_release.py [版本号]         # 默认最新; 本地调试(覆盖)
py -3 scripts/build_release.py 15.7.0 --release # 正式发布: 递增修订号 -r<n>, 不覆盖
```

## 结构

```
release/<版本号>[/-r<n>]/
├── standard/                 # 标准版(缩写键)
│   ├── zh/LC_MESSAGES/global.mo            # 完整版(国服简中, 无 loader 用)
│   ├── zh/LC_MESSAGES/wowsZhShipnameFixes.mo   # 增量版(国服, loader 用)
│   ├── zh_sg/LC_MESSAGES/global.mo         # 完整版(国际服简中, 无 loader 用)
│   ├── zh_sg/LC_MESSAGES/wowsZhShipnameFixes.mo  # 增量版(国际服, loader 用)
│   └── version.txt
└── full/                     # 全名版(缩写键用 _FULL, 结构同 standard)
```

- **无 loader**：取 `standard/`（或 `full/`）的 `zh/`（或 `zh_sg/`）`LC_MESSAGES/global.mo` 放进 `res_mods/texts/<语言>/LC_MESSAGES/`
- **有 loader（阿斯兰）**：取同目录下的 `wowsZhShipnameFixes.mo` 放进 `res_mods/texts/<语言>/`（任意深度），由 loader 加载

## 机制

- **完整版**：官方该语言键集合 + 舰船键覆盖为最终翻译（`full` 版先把缩写键换为 `_FULL` 值）；用自定义编译器遍历全部条目（含空翻译键，避免显示键值）
- **增量版**：只保留「最终翻译 ≠ 官方 zh/zh_sg 任一」的舰船键，`Priority: 50`；同一份复制到 zh / zh_sg

## 打包

```
py -3 scripts/package_release.py [版本号(-r)]
```

输出 **4 种组合** zip（`dist/`，不上传）：

| zip | 含义 |
|---|---|
| `<版本>-global-standard` | **完全替换翻译文件**（完整版）+ **标准版**（缩写键） |
| `<版本>-global-full` | **完全替换翻译文件**（完整版）+ **全称版**（`_FULL`） |
| `<版本>-inc-standard` | **增量**（已安装阿斯兰）+ **标准版** |
| `<版本>-inc-full` | **增量**（已安装阿斯兰）+ **全称版** |

- `*-global`：**完全替换翻译文件**，给**未安装 Localization Loader** 的玩家
- `*-inc`：**增量**（只改差异，其余回落官方），给**已安装阿斯兰 / Localization Loader** 的玩家
- `-standard`：**标准版**（缩写键）；`full`：**替换为全称**（`_FULL` 完整船名）

内部 `res_mods/texts/<zh|zh_sg>/LC_MESSAGES/<对应 mo>`；也可用手动工作流发布为 Release。

## 要点

- 完整版命名 `global.mo`（传统方式）；增量版命名 **`wowsZhShipnameFixes.mo`**（不叫 global.mo，避免被 loader 忽略）
- 增量只含改动键，避免「整份目录拷贝」的冲突、臃肿、随版本更新问题
- 每个发布目录含 `version.txt`（mod版本 / 游戏版本 / 类型 / 语言 / 完整+增量键数 / 构建时间）
