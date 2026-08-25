# 自动同步工作流

工作流文件：`.github/workflows/sync-translations.yml`

## 触发方式

- **定时**：每天 03:00 UTC（北京时间 11:00）自动检查 ModSDK 新版本
- **手动**：GitHub Actions 页面点击 **Run workflow** 立即执行

## 处理流程

1. **安装依赖**：`polib`（mo 解析）、`openpyxl`（表格生成）
2. **同步翻译**（`scripts/sync_translations.py`）：
   - 查询 [wgmods/ModSDK](https://github.com/wgmods/ModSDK) 最新 tag
   - 与本地已有版本比较，有新版本时用 raw URL 直接下载三个语言的 `.mo` 文件
   - 修复 `.mo` 文件头（wgmods 元数据换行符丢失，需重建后才能解析）
   - 用 polib 反编译为 `.po`，导出 `global.csv`（全部词条）与 `ship.csv`（舰船词条）
   - 已同步版本若 CSV 缺失会自动补生成
   - 生成版本 `README.md`
3. **生成表格**（`scripts/generate_tables.py`）：
   - 自动检测最新两个版本，生成 `global.xlsx` / `ship.xlsm` / 差异表
   - **增量生成**：已存在的文件跳过（保护人工翻译），详见 [表格与差异生成](tables.md)
   - **翻译迁移**：从旧版本 ship.xlsm 按键值迁移最终翻译
4. **提交推送**：全部变更自动 commit 并 push，推送显式携带 token 认证，5 分钟超时防挂起

## 注意事项

- 语言目录名是 **`zh_sg`（下划线）**，不是连字符
- 旧版本目录**永远保留**，不会因新版本同步而删除
- workflow 推送使用 `GITHUB_TOKEN`（`contents: write` 权限）
