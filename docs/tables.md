# 表格与差异生成

脚本：`scripts/generate_tables.py`

```
py -3 scripts/generate_tables.py            # 自动取最新两个版本
py -3 scripts/generate_tables.py <新版本> <旧版本>
py -3 scripts/generate_tables.py --force   # 强制重建
```

## 生成产物

| 文件 | 说明 |
|---|---|
| `global.xlsx` | 三语言对照表（键值/zh/zh_sg/en/最终翻译，不着色） |
| `ship.xlsm` | 舰船词条表（模板 + VB 宏自动配色，翻译入口） |
| `global_diff.xlsx` | 全部词条相对上一版本的差异 |
| `ship_diff.xlsx` | 舰船词条差异（最终翻译列留空） |

## 幂等与迁移

- 默认只生成缺失文件（已存在跳过，保护人工翻译）；强制重建加 `--force`
- `--force` 重建 `ship.xlsm` 时先读回现有最终翻译再写回，不丢失
- 翻译迁移优先级：目标自身 > 旧版本 `ship.xlsm`（补漏）；新增键留空待填

## 差异判定

新增：键只在新版本；删除：键只在旧版本；修改：zh / zh_sg / en 任一列不同。

## 复数条目

官方 `.mo` 部分键为 gettext 复数条目（`msgid_plural`），导出 CSV 取第一个复数形式（zh/zh_sg `nplurals=1`），避免游戏显示键值。

## 格式

- 数据区按列：中文列（zh/zh_sg/最终翻译/差异等）用**微软雅黑**，英文/拉丁列（键值/en）用**Arial**
- `ship.xlsm` 数据行高 **16.3**；表头 Arial 粗体白字 + 蓝色填充
- 模板默认字体已从宋体改为微软雅黑，非通用字体（如 HarmonyOS Sans SC）已替换

## 幽灵行防护

- `purge_ghost_rows`：清理数据行后的幽灵空行
- `verify_xml_clean`：生成后四重验证（row 最大行号/单元格引用/sqref/definedNames），超范围即报错拒收
