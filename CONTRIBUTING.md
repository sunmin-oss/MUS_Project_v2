# 貢獻指南 (Contributing Guide)

本文件規範了 **MUS2（藥知道）藥物辨識系統** 專案的 Git 工作流程、分支命名、版號規則與各情境操作流程，所有協作成員須遵守。

---

## 目錄

1. [分支策略](#分支策略)
2. [分支命名規範](#分支命名規範)
3. [版號規範](#版號規範)
4. [Commit Message 規範](#commit-message-規範)
5. [各情境操作流程](#各情境操作流程)
6. [快速參考](#快速參考)

---

## 分支策略

本專案採用簡化版 **Git Flow**，共有以下幾種分支類型：

### 主要分支（長期存在，禁止直接 push）

| 分支 | 用途 |
|------|------|
| `main` | 生產環境，僅接受來自 `release/*` 或 `hotfix/*` 的 merge |
| `develop` | 整合分支，所有功能與修復完成後先 merge 至此 |

### 輔助分支（短暫存在，完成後須刪除）

| 分支 | 用途 |
|------|------|
| `feature/<描述>` | 開發新功能 |
| `fix/<描述>` | 修復非緊急 bug |
| `hotfix/<描述>` | 修復線上緊急 bug（從 `main` 開出） |
| `release/<版本號>` | 準備發布，僅允許小 bug 修復與版號更新 |

---

## 分支命名規範

- 全部使用**小寫英文**，單字之間以 `-` 連接
- 禁止使用無意義名稱（例如：`this`、`temp`、`test123`）

```
# 正確範例
feature/gemini-rag-mode
feature/prescription-ocr
feature/nhi-crawler-cache
fix/drug-search-fallback
fix/image-upload-validation
hotfix/critical-api-crash
release/v1.2.0

# 錯誤範例
this
4/24-temp
newfeature
fix1
```

---

## 版號規範

採用 **Semantic Versioning (語意化版本)**，格式為：

```
v主版本.次版本.修補版本
vMAJOR.MINOR.PATCH
```

| 版號欄位 | 何時遞增 | 範例 |
|---------|---------|------|
| **MAJOR** | 破壞性變更，API 不相容舊版 | `v1.3.0 → v2.0.0` |
| **MINOR** | 新增向下相容的功能 | `v1.1.0 → v1.2.0` |
| **PATCH** | Bug 修復，不影響 API 介面 | `v1.2.0 → v1.2.1` |

升版規則：
- 升 MAJOR 時，MINOR 與 PATCH 歸零
- 升 MINOR 時，PATCH 歸零
- 目前開發初期版本使用 `v0.x.x`，正式對外發布後升為 `v1.0.0`

> **注意**：PATCH 版號是跟著 **release 動作**升版，不是每個 fix branch 完成就升一次。多個 fix 可累積後一起在同一個 release 中升版。

---

## Commit Message 規範

採用 **Conventional Commits** 格式：

```
<type>(<scope>): <簡短描述>

[選填] 詳細說明

[選填] 關聯 issue：Closes #issue號碼
```

### Type 清單

| Type | 用途 |
|------|------|
| `feat` | 新增功能 |
| `fix` | 修復 bug |
| `docs` | 文件更新 |
| `refactor` | 重構（不影響功能） |
| `test` | 新增或修改測試 |
| `chore` | 雜項（更新套件、設定檔等） |
| `hotfix` | 緊急線上修復 |

### Scope 建議（依模組命名）

| Scope | 對應模組 |
|-------|----------|
| `api` | Flask API 端點 (main.py) |
| `vision` | 視覺辨識模組 (vision_api_*.py) |
| `db` | 藥物資料庫 (drug_database.py) |
| `crawler` | NHI/TFDA 爬蟲 (nhi_crawler.py) |
| `admin` | 管理員後台 (admin_routes.py) |
| `frontend` | 前端頁面 (index.html, admin.html) |
| `config` | 配置管理 (config.py) |
| `docker` | Docker 部署相關 |

### 範例

```
feat(vision): 新增 Gemini RAG 模式藥物辨識
feat(frontend): 新增藥單拍照辨識頁面
feat(crawler): 整合 NHI 爬蟲快取機制
fix(db): 修復藥物模糊搜尋結構相容問題
fix(api): 修復圖片上傳檔案大小驗證
docs(api): 更新 API 端點文件
refactor(vision): 將 RAG 提示詞邏輯拆分至獨立方法
chore: 更新 requirements.txt 套件版本
hotfix(api): 修復辨識端點回應格式錯誤
```

---

## 各情境操作流程

### 情境一：一般功能開發 / Bug 修復

多個成員同時開發不同功能，各自在自己的分支上作業，完成後合併回 `develop`。

```
feature/gemini-rag-mode     ──┐
feature/prescription-ocr    ──┤  各自開發完成後 merge 回 develop
fix/drug-search-fallback    ──┘
                                 ↓
                             develop  ←── 整合所有功能、內部確認
```

**步驟：**
1. 從 `develop` 建立自己的 feature 或 fix 分支
2. 在該分支上開發並 commit
3. 確認功能正常後，merge 回 `develop`
4. 刪除該分支

---

### 情境二：發布新版本 (Release)

當 `develop` 累積足夠功能或達到里程碑時進行 release。

```
feature/xxx  ──┐
feature/yyy  ──┤
fix/zzz      ──┘
                ↓ merge
            develop  ←── 整合、內部測試
                ↓ 時機到了
         release/v1.2.0  ←── 給 QA／測試（只允許修小 bug）
                ↓ 測試通過
              main  (建立 Tag v1.2.0)
                ↓ 同步
            develop  ←── 把測試期間的修復同步回來
```

**步驟：**
1. 從 `develop` 建立 release 分支，命名為 `release/v版本號`
2. 在 release 分支上只允許修復測試期間發現的小 bug，不得新增功能
3. 測試通過後，merge 至 `main` 並在 GitHub 上建立版本 Tag（例如 `v1.2.0`）
4. 同步 merge 回 `develop`，確保測試期間的修復不遺漏
5. 刪除 release 分支

> **建議 Release 頻率**：每個功能里程碑完成時，或固定每週一次。

---

### 情境三：緊急修復 (Hotfix)

當線上 `main` 發現嚴重 bug 需要立即修復，不能等下一個 release。

```
              main (v1.2.0)
                ↓ 從 main 開出
        hotfix/critical-crash  ←── 緊急修復
                ↓ 修復完成
              main  (建立 Tag v1.2.1)
                ↓ 同步
            develop  ←── 確保修復內容不遺漏
```

**步驟：**
1. 從 `main` 建立 hotfix 分支，命名為 `hotfix/<問題描述>`
2. 修復完成後，merge 至 `main` 並在 GitHub 上建立新的 PATCH 版本 Tag（例如 `v1.2.1`）
3. 同步 merge 回 `develop`，確保修復內容不遺漏
4. 刪除 hotfix 分支

---

### 禁止事項

- 禁止直接 push 至 `main`
- 禁止 force push 至 `main` 或 `develop`

---

## 快速參考

| 情境 | 流程 |
|------|------|
| 新功能開發 | `develop` → `feature/xxx` → merge → `develop` |
| Bug 修復 | `develop` → `fix/xxx` → merge → `develop` |
| 發布版本 | `develop` → `release/vX.Y.Z` → 測試 → `main`（打 Tag）→ 同步 `develop` |
| 緊急修復 | `main` → `hotfix/xxx` → `main`（打 Tag）→ 同步 `develop` |
