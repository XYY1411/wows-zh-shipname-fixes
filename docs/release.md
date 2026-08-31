# mod 发布构建

`scripts/build_release.py` 生成**增量**发布（只含修正的舰船键），供 **TTaro Localization Loader**（阿斯兰自动安装）加载；`scripts/package_release.py` 打包。

## 构建

```
py -3 scripts/build_release.py [版本号]         # 默认最新; 本地调试(覆盖)
py -3 scripts/build_release.py 15.7.0 --release # 正式发布: 递增修订号 -r<n>, 不覆盖
```

## 结构

```
release/<版本号>[/-r<n>]/
├── standard/                 # 标准版(缩写键)
│   ├── zh/LC_MESSAGES/wowsZhShipnameFixes.mo      # 国服简中
│   ├── zh_sg/LC_MESSAGES/wowsZhShipnameFixes.mo   # 国际服简中
│   └── version.txt
└── full/                     # 全名版(缩写键用 _FULL, 结构同 standard)
```

玩家取 `standard/`（或 `full/`）放进 `res_mods/texts/`（保留 zh / zh_sg 层级），由 Localization Loader 加载。

## 增量规则

- **只输出差异键**：最终翻译 ≠ 官方 **zh（国服）** 或 **zh_sg（国际服）** 任一不同才计入
- `full` 版把无后缀键 `IDS_P?S????` 替换为对应 `_FULL` 的完整船名后再算差异
- 增量为同一份，同时放到 zh / zh_sg 两个语言目录（对无需改动的键覆盖后仍等于官方，安全）
- **`X-LocalizationLoader-Priority: 50`**（缺省值，非必须；共存的翻译 mod 按优先级裁决）

## 流程

`ship.xlsm` → 最终翻译 → 对比 zh + zh_sg 官方 → 取差异键 → 生成增量 `.mo`（`wowsZhShipnameFixes.mo`，含优先级头）→ 复制到 zh / zh_sg → `version.txt`。

## 打包

```
py -3 scripts/package_release.py [版本号(-r)]
```

输出 `dist/<版本号>-standard.zip` / `-full.zip`，内部 `res_mods/texts/<zh|zh_sg>/LC_MESSAGES/wowsZhShipnameFixes.mo`；或用手动工作流发布为 Release。

## 要点

- 命名不用 `global.mo`（会被游戏自身的 overlay 占用并整体替换），用 **`wowsZhShipnameFixes.mo`**
- 只含改动键，避免「整份目录拷贝」的冲突、臃肿、随版本更新问题
- 每个发布目录含 `version.txt`（mod版本 / 游戏版本 / 类型 / 语言 / 变更键数 / 构建时间）
