# 論文圖表素材索引

> 本資料夾包含專題論文所需的所有圖、表、程式碼片段與系統截圖。
> 圖表編號依照論文中出現順序排列。

---

## 一、系統截圖 (`系統截圖/`)

截圖為瀏覽器即時擷取，解析度約 820×900px。

| 編號 | 截圖內容 | 對應章節 | 備註 |
|------|---------|---------|------|
| SS-01 | 登入頁面 | 3.9 | 帳號密碼登入表單 |
| SS-02 | 首頁（歡迎畫面） | 4.2 | 五大功能入口 |
| SS-03 | 藥物搜尋結果 | 4.2 | 搜尋「普拿疼」8 筆結果 |
| SS-04 | 藥物詳情頁 | 4.2 | 普拿疼膜衣錠 500mg |
| SS-05 | 用藥清單頁 | 4.2 | 時段篩選 + 藥單管理 |
| SS-06 | AI 諮詢頁 | 4.2 | AI 藥物諮詢功能 |
| SS-07 | 個人設定頁 | 4.2 | 主題色、字體、安全設定 |
| SS-08 | 管理後台 — 儀表板 | 4.6 | 統計卡片 + API 請求表 |
| SS-09 | 管理後台 — 藥物管理 | 4.6 | 藥物列表 + 圖片 |
| SS-10 | 管理後台 — 批次更新 | 4.6 | 更新控制 + 進度條 |
| SS-11 | 管理後台 — API 統計 | 4.6 | 每日請求圖表 |

> **注意**：截圖目前存在瀏覽器預覽中（無法直接匯出為檔案）。
> 建議使用 Windows Snipping Tool 或論文截圖時從瀏覽器重新擷取。

---

## 二、架構與流程圖 (`架構與流程圖/`)

格式為 Mermaid 原始碼（.md），可透過以下方式轉為圖片：
1. **VS Code 插件**：安裝 `Markdown Preview Mermaid Support` 後在預覽視窗截圖
2. **Mermaid Live**：https://mermaid.live 貼上程式碼後匯出 PNG/SVG
3. **CLI**：`npx @mermaid-js/mermaid-cli mmdc -i file.md -o output.png`

| 編號 | 圖表名稱 | 檔案 | 對應章節 | 類型 |
|------|---------|------|---------|------|
| 圖 1 | 系統整體架構圖 | fig_01_system_architecture.md | 2.3, 3.1 | graph TB |
| 圖 2 | RAG 辨識流程圖 | fig_02_rag_flow.md | 3.3 | flowchart |
| 圖 3 | 處方箋 OCR 流程圖 | fig_03_ocr_flow.md | 3.4 | flowchart |
| 圖 4 | AI Provider 路由架構圖 | fig_04_ai_routing.md | 3.5 | flowchart |
| 圖 5 | 四層安全檢查流程圖 | fig_05_safety_check.md | 3.6 | flowchart |
| 圖 6 | 爬蟲批次更新流程圖 | fig_06_crawler_flow.md | 3.7 | flowchart |
| 圖 7 | 資料庫 ER 圖 | fig_07_er_diagram.md | 3.8 | erDiagram |
| 圖 8 | JWT 認證流程圖 | fig_08_jwt_auth.md | 3.9 | sequence |

---

## 三、程式碼片段 (`程式碼片段/`)

精簡後的關鍵程式碼，適合論文中以 Listing 形式呈現。

| 編號 | 程式碼內容 | 檔案 | 對應章節 | 原始檔案 |
|------|----------|------|---------|---------|
| Code 1 | RAG 辨識核心提示詞 | code_01_rag_prompt.py | 3.3 | vision_api_gemini.py |
| Code 2 | 藥物特徵提取 | code_02_drug_features.py | 3.3 | drug_database.py |
| Code 3 | AI 路由與熔斷器 | code_03_ai_router.py | 3.5 | services/ai/recognizer_router.py |
| Code 4 | 四層安全檢查 | code_04_safety_check.py | 3.6 | services/__init__.py |
| Code 5 | 藥單 OCR 處方箋辨識 | code_05_ocr_prescription.py | 3.4 | vision_api_gemini.py |
| Code 6 | 批次更新管理器 | code_06_batch_update.py | 3.7 | scripts/batch_update.py |

---

## 四、比較表格 (`比較表格/`)

| 編號 | 表格名稱 | 檔案 | 對應章節 |
|------|---------|------|---------|
| 表 I | RAG vs 傳統 LLM 辨識 | table_01_rag_vs_traditional.md | 4.1 |
| 表 II | MUS v1 vs v2 比較 | table_02_v1_vs_v2.md | 4.2 |
| 表 III | OCR 提取準確度 | table_03_ocr_accuracy.md | 4.3 |
| 表 IV | API 回應時間統計 | table_04_api_response_time.md | 4.4 |
| 表 V | 技術棧總覽 | table_05_tech_stack.md | 3.1 |
| 表 VI | 功能比較（同類產品） | table_06_product_comparison.md | 4.5 |
| 表 VII | 創新分類與實驗對應 | table_07_innovation_mapping.md | 3.2, 4.8 |
| 表 VIII | 批次更新效能優化 | table_08_batch_optimization.md | 3.7 |
| 表 IX | 資料庫統計數據 | table_09_database_stats.md | 4.6 |

---

## 五、論文中圖表使用建議

### 格式要求（依學校論文格式）
- 圖片寬度：7.7cm（單欄寬度）或 16cm（雙欄跨頁）
- 圖片解析度：至少 300 DPI
- 圖標題格式：「圖 1. 系統整體架構圖」（置於圖下方）
- 表標題格式：「表 I. RAG 辨識 vs 傳統 LLM 辨識比較」（置於表上方）
- 字體：標楷體（中文）/ Times New Roman（英文），10pt

### 建議排版順序
1. **前言**：無圖表
2. **研究目的**：表 II（v1 vs v2）
3. **原理與分析**：圖 1~8、表 V、VII、VIII、Code 1~6
4. **實驗結果**：表 I、III、IV、VI、IX、SS-01~11
5. **結論**：無圖表（或引用前述圖表）

### 論文頁數控制（4~6 頁）
建議精選 4~5 張圖 + 3~4 張表即可，不需全部使用。
優先選用：圖 1（架構）、圖 2（RAG）、表 I（RAG 比較）、表 II（v1 vs v2）、SS-02（首頁）、SS-08（後台）。
