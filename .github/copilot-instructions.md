# Copilot 專案指令

## Git 操作規範

執行任何 git 操作（commit、branch、merge、tag、push）前，必須遵守 `CONTRIBUTING.md` 中的規範：

### 分支規則
- **禁止**直接在 `main` 上 commit 或 push
- 功能開發：從 `develop` 開出 `feature/<描述>`，完成後 merge 回 `develop`
- Bug 修復：從 `develop` 開出 `fix/<描述>`，完成後 merge 回 `develop`
- 緊急修復：從 `main` 開出 `hotfix/<描述>`，修復後 merge 回 `main` 和 `develop`
- 發布版本：從 `develop` 開出 `release/v版號`，測試通過後 merge 至 `main`（打 Tag）再同步 `develop`
- 分支名稱全小寫英文，用 `-` 連接

### Commit Message 格式
```
<type>(<scope>): <簡短描述>
```
- **type**：feat / fix / docs / refactor / test / chore / hotfix
- **scope**（英文）：api / vision / db / crawler / admin / frontend / config / docker
- 描述用中文
- 範例：`feat(frontend): 新增藥單拍照辨識頁面`

### 版號
- 格式：`vMAJOR.MINOR.PATCH`（Semantic Versioning）
- 版號更新必須走 release 分支流程

### 操作前確認
1. 先用 `git branch --show-current` 確認目前分支
2. 如果在 `main` 上且非 hotfix/release merge，提醒使用者切換分支
3. commit 前確認 message 符合 Conventional Commits 格式
