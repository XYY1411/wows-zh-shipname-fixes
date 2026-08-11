# 表格与差异生成

脚本：`scripts/generate_tables.py`

```
python scripts/generate_tables.py            # 自动取最新两个版本
python scripts/generate_tables.py <新版本> <旧版本>
```

## 生成产物

| 文件 | 说明 |
|---|---|
| `global.xlsx` | 三语言对照表：键值 / 简体中文 / 简体中文新加坡 / 英文 / 最终翻译（不着色） |
| `ship.xlsm` | 舰船词条表：基于 `templates/ship_template.xlsm`，VB 宏与布局完全一致（E 列配色、BCD 关系配色、A 列系别×舰种配色） |
| `global_diff.xlsx` | 新版本相对上一版本的全部词条差异（新增/删除/修改，新旧翻译并排对比） |
| `ship_diff.xlsx` | 仅舰船词条的差异，**最终翻译列留空**（不对比最终翻译） |

## 翻译迁移

生成新版本 `ship.xlsm` 时，自动读取**旧版本** `ship.xlsm` 的最终翻译列（E 列），
按键值（A 列）迁移到新版本对应行：

- 旧版本已有的键 → 迁移最终翻译
- **新增键 → 最终翻译留空**，待人工填写
- 旧版本 `ship.xlsm` 已存在则**跳过不覆盖**，保护人工翻译

## 差异判定规则

- **新增**：键只在新版本出现
- **删除**：键只在旧版本出现
- **修改**：键在两边都有，但 zh / zh_sg / en 任一列不同（含尾随空格等不可见字符差异）

## 格式约定

- 数据区使用 **Consolas** 等宽字体（系统自带，无需安装）
- 表头：Arial 粗体白字 + 蓝色填充 `FF4472C4`
- 字体已净化：模板中的非通用字体（如 HarmonyOS Sans SC）已替换为 Arial

## 幽灵行防护

生成时两道防线：

1. **`purge_ghost_rows`**：清理数据行之后的幽灵空行（有样式无内容）
2. **`verify_xml_clean`**：生成后四重验证，任何一项超出数据行立即报错拒收：
   - row 元素最大行号（覆盖所有列）
   - 单元格引用最大行号（任意列，如 E 列远端）
   - 条件格式 / 数据验证 sqref 引用范围
   - workbook 打印区域 definedNames 引用范围

> 已知现象：openpyxl 生成的 xlsm 在部分 Excel 环境首次打开时可能显示滚动条空白
> （UsedRange 被临时撑大），打开后宏运行即自动归位，不影响文件本身。
