# 表 IV：API 回應時間統計
# 用途：論文 4.4 節

| API 端點 | 平均回應時間 | 90th 百分位 | 功能說明 |
|---------|-----------|-----------|---------|
| GET /api/health | <1 ms | 1 ms | 健康檢查 |
| POST /api/auth/login | 50 ms | 80 ms | 使用者登入 |
| POST /api/search | 30-80 ms | 150 ms | 藥物搜尋 |
| GET /api/drug/:id | 1-2 ms | 5 ms | 藥物詳情（本地） |
| GET /api/drug/:id (NHI) | 1.5-2s | 3s | 藥物詳情（含爬蟲） |
| POST /api/recognize | 3-5s | 8s | RAG 藥物辨識 |
| POST /api/recognize_prescription | 3-5s | 8s | 處方箋 OCR |
| POST /api/safety/check | 10 ms | 30 ms | 安全檢查 |
| GET /api/user/medications | 5 ms | 15 ms | 用藥清單 |
| POST /api/consult | 2-4s | 6s | AI 諮詢 |
