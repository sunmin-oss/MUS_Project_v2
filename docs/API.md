# MUS2 藥物辨識系統 — API 文件

> 版本：v3.0.0 | 最後更新：2026-05-27
> Base URL：`http://localhost:5000`

---

## 目錄

1. [認證機制](#認證機制)
2. [系統端點](#系統端點)
3. [Auth 認證](#auth-認證)
4. [Profile 成員管理](#profile-成員管理)
5. [藥物辨識](#藥物辨識)
6. [藥物搜尋與查詢](#藥物搜尋與查詢)
7. [用藥管理 Medications](#用藥管理-medications)
8. [服藥紀錄 Adherence](#服藥紀錄-adherence)
9. [Push Token 管理](#push-token-管理)
10. [安全檢查 Safety](#安全檢查-safety)
11. [錯誤碼對照](#錯誤碼對照)

---

## 認證機制

本系統使用 **JWT (JSON Web Token)** 進行認證。

### 取得 Token

呼叫 `POST /api/auth/login` 取得 `access_token` 和 `refresh_token`。

### 使用 Token

在需要認證的端點，於 Header 中加入：

```
Authorization: Bearer <access_token>
```

### Token 有效期

| Token 類型 | 有效期 | 用途 |
|---|---|---|
| Access Token | 15 分鐘 | API 請求認證 |
| Refresh Token | 7 天 | 刷新 Access Token |

### Rate Limit

- 全域預設：**200 次 / 分鐘**
- `/api/recognize`：**30 次 / 分鐘**

超過限制回傳 `429 Too Many Requests`。

---

## 系統端點

### `GET /api/health`

檢查系統狀態。**不需認證。**

**回應 200：**
```json
{
  "status": "healthy",
  "timestamp": "2026-05-27T10:00:00",
  "services": {
    "vision_api": "ready",
    "database": "ready"
  }
}
```

**回應 503（降級）：**
```json
{
  "status": "degraded",
  "timestamp": "...",
  "services": {
    "vision_api": "unavailable",
    "database": "ready"
  }
}
```

---

## Auth 認證

### `POST /api/auth/register`

使用者註冊。

**請求：**
```json
{
  "username": "alice",
  "password": "StrongP@ss1",
  "display_name": "小明"
}
```

| 欄位 | 類型 | 必填 | 說明 |
|---|---|---|---|
| username | string | ✅ | 3–32 字元，英數字/底線/連字號 |
| password | string | ✅ | 至少 8 字元 |
| display_name | string | ❌ | 顯示名稱，預設同 username |

**回應 201：**
```json
{
  "success": true,
  "user_id": 1,
  "message": "註冊成功"
}
```

**錯誤：**
| 狀態碼 | 情境 |
|---|---|
| 400 | 帳號/密碼不符規則 |
| 409 | 使用者名稱已被使用 |

---

### `POST /api/auth/login`

使用者登入，取得 JWT Token。

**請求：**
```json
{
  "username": "alice",
  "password": "StrongP@ss1"
}
```

**回應 200：**
```json
{
  "success": true,
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "user": {
    "id": 1,
    "username": "alice",
    "display_name": "小明",
    "is_active": true,
    "created_at": "2026-05-27T10:00:00"
  }
}
```

**錯誤：**
| 狀態碼 | 情境 |
|---|---|
| 400 | 缺少帳號或密碼 |
| 401 | 帳號或密碼錯誤 |
| 403 | 帳號已停用 |

---

### `POST /api/auth/refresh`

🔒 **需認證（Refresh Token）**

刷新 Access Token。Header 使用 **Refresh Token**。

**回應 200：**
```json
{
  "success": true,
  "access_token": "eyJ..."
}
```

---

### `POST /api/auth/logout`

🔒 **需認證**

撤銷目前的 Access Token。

**回應 200：**
```json
{
  "success": true,
  "message": "已登出"
}
```

---

### `GET /api/auth/me`

🔒 **需認證**

取得目前登入使用者資訊。

**回應 200：**
```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "alice",
    "display_name": "小明",
    "is_active": true,
    "created_at": "2026-05-27T10:00:00"
  }
}
```

---

## Profile 成員管理

支援家庭多人成員用藥管理。

### `GET /api/auth/profiles`

🔒 **需認證**

列出目前使用者的所有 Profile。

**回應 200：**
```json
{
  "success": true,
  "profiles": [
    {
      "id": 1,
      "user_id": 1,
      "name": "爸爸",
      "birth_date": "1965-03-15",
      "gender": "male",
      "note": "高血壓",
      "is_default": true,
      "created_at": "2026-05-27T10:00:00"
    }
  ]
}
```

---

### `POST /api/auth/profiles`

🔒 **需認證**

新增 Profile。

**請求：**
```json
{
  "name": "媽媽",
  "birth_date": "1968-07-20",
  "gender": "female",
  "note": "糖尿病"
}
```

| 欄位 | 類型 | 必填 | 說明 |
|---|---|---|---|
| name | string | ✅ | 成員名稱 |
| birth_date | string | ❌ | YYYY-MM-DD |
| gender | string | ❌ | male / female / other |
| note | string | ❌ | 備註 |

**回應 201：**
```json
{
  "success": true,
  "profile": { ... }
}
```

---

### `PUT /api/auth/profiles/<profile_id>`

🔒 **需認證**

更新 Profile。

**請求（部分更新）：**
```json
{
  "name": "媽媽（更新）",
  "note": "糖尿病、高血脂"
}
```

**回應 200：**
```json
{
  "success": true,
  "profile": { ... }
}
```

---

### `DELETE /api/auth/profiles/<profile_id>`

🔒 **需認證**

刪除 Profile。

**回應 200：**
```json
{
  "success": true,
  "message": "Profile 已刪除"
}
```

---

## 藥物辨識

### `POST /api/recognize`

上傳藥物圖片進行 AI 辨識。**不需認證**（但帶 JWT 可啟用安全檢查）。

Rate Limit：**30 次 / 分鐘**

**請求：** `multipart/form-data`

| 欄位 | 類型 | 必填 | 說明 |
|---|---|---|---|
| image | file | ✅ | 藥物圖片（png/jpg/jpeg/gif/bmp/webp） |
| language | string | ❌ | `zh`（預設）或 `en` |

**回應 200：**
```json
{
  "success": true,
  "request_id": "drug",
  "recognized_items": [
    {
      "name": "普拿疼",
      "confidence": 0.95,
      "drug_id": 123,
      "source": "gemini_rag",
      "reason": "外觀特徵匹配",
      "images": [],
      "details": {
        "chinese_name": "普拿疼加強錠",
        "english_name": "PANADOL EXTRA",
        "license_number": "衛署藥輸字第012345號",
        "shape": "橢圓形",
        "color": "白色",
        "usage": "解熱鎮痛"
      }
    }
  ],
  "message": "辨識完成，找到 1 個匹配結果",
  "safety_warnings": [
    {
      "drug_id": 123,
      "name": "普拿疼",
      "overall": "warning",
      "checks": [ ... ]
    }
  ]
}
```

> `safety_warnings` 僅在帶有效 JWT 且辨識出的藥物有安全疑慮時出現。

**錯誤：**
| 狀態碼 | 情境 |
|---|---|
| 400 | 未上傳圖片 / 不支援的格式 |
| 413 | 檔案超過 10MB |
| 429 | 超過 rate limit |
| 503 | Vision API 暫不可用 |

---

### `POST /api/recognize_prescription`

上傳藥單圖片進行 OCR 辨識。**不需認證。**

**請求：** `multipart/form-data`

| 欄位 | 類型 | 必填 | 說明 |
|---|---|---|---|
| image | file | ✅ | 藥單圖片 |

**回應 200：**
```json
{
  "success": true,
  "request_id": "prescription",
  "recognized_drugs": ["普拿疼", "Amoxicillin"],
  "recognized_items": [
    {
      "name": "普拿疼",
      "confidence": 1.0,
      "source": "prescription",
      "drug_id": 123,
      "details": { ... },
      "images": []
    }
  ],
  "message": "辨識完成，找到 2 種藥物"
}
```

---

## 藥物搜尋與查詢

### `POST /api/search`

藥物名稱搜尋（先查資料庫，無結果再用 Gemini AI）。**不需認證。**

**請求：**
```json
{
  "query": "普拿疼",
  "limit": 5
}
```

| 欄位 | 類型 | 必填 | 說明 |
|---|---|---|---|
| query | string | ✅ | 搜尋關鍵字（至少 2 字） |
| limit | integer | ❌ | 回傳筆數上限（預設 10，最大 20） |

**回應 200：**
```json
{
  "success": true,
  "results": [
    {
      "id": 123,
      "chinese_name": "普拿疼加強錠",
      "english_name": "PANADOL EXTRA",
      "license_number": "...",
      "images": []
    }
  ],
  "total": 1,
  "source": "database"
}
```

| source 值 | 說明 |
|---|---|
| `database` | 本地資料庫搜尋結果 |
| `gemini` | Gemini AI 搜尋結果 |

---

### `GET /api/drug/<drug_id>`

取得單一藥物詳細資訊（含 NHI/TFDA 副作用、適應症）。**不需認證。**

**回應 200：**
```json
{
  "success": true,
  "drug": {
    "id": 123,
    "chinese_name": "普拿疼加強錠",
    "english_name": "PANADOL EXTRA",
    "license_number": "...",
    "manufacturer": "...",
    "shape": "橢圓形",
    "color": "白色",
    "usage": "解熱鎮痛",
    "images": [],
    "nhi_details": {
      "side_effects": "...",
      "indications": "...",
      "contraindications": "..."
    }
  }
}
```

---

## 用藥管理 Medications

### `GET /api/user/medications`

🔒 **需認證**

列出用藥紀錄。

**Query 參數：**
| 參數 | 類型 | 說明 |
|---|---|---|
| profile_id | integer | 篩選特定成員 |
| active | string | `true`（預設）僅顯示啟用中 |

**回應 200：**
```json
{
  "success": true,
  "medications": [
    {
      "id": 1,
      "user_id": 1,
      "profile_id": 1,
      "drug_id": 123,
      "name": "普拿疼",
      "dosage": "500mg",
      "unit": "錠",
      "frequency": "daily",
      "duration_days": 7,
      "start_date": "2026-05-27",
      "end_date": "2026-06-03",
      "stock_qty": 14,
      "note": "飯後服用",
      "is_active": true,
      "schedules": [
        {
          "id": 1,
          "time_slot": "morning",
          "scheduled_time": "08:00:00",
          "dose_qty": 1.0
        }
      ],
      "created_at": "2026-05-27T10:00:00"
    }
  ]
}
```

---

### `POST /api/user/medications`

🔒 **需認證**

新增用藥。

**請求：**
```json
{
  "name": "普拿疼",
  "profile_id": 1,
  "drug_id": 123,
  "dosage": "500mg",
  "unit": "錠",
  "frequency": "daily",
  "duration_days": 7,
  "start_date": "2026-05-27",
  "end_date": "2026-06-03",
  "stock_qty": 14,
  "note": "飯後服用",
  "schedules": [
    {
      "time_slot": "morning",
      "scheduled_time": "08:00",
      "dose_qty": 1.0
    },
    {
      "time_slot": "evening",
      "scheduled_time": "20:00",
      "dose_qty": 1.0
    }
  ]
}
```

| 欄位 | 類型 | 必填 | 說明 |
|---|---|---|---|
| name | string | ✅ | 藥物名稱 |
| profile_id | integer | ✅ | 家庭成員 ID |
| drug_id | integer | ❌ | 關聯藥物資料庫 ID |
| dosage | string | ❌ | 劑量 |
| unit | string | ❌ | 單位（錠/ml/包…） |
| frequency | string | ❌ | daily / twice_daily / weekly（預設 daily） |
| duration_days | integer | ❌ | 療程天數 |
| start_date | string | ❌ | YYYY-MM-DD（預設今天） |
| end_date | string | ❌ | YYYY-MM-DD |
| stock_qty | integer | ❌ | 庫存數量 |
| note | string | ❌ | 備註 |
| schedules | array | ❌ | 排程列表 |

**回應 201：**
```json
{
  "success": true,
  "medication": { ... }
}
```

---

### `GET /api/user/medications/<med_id>`

🔒 **需認證**

取得單一用藥詳細。

---

### `PUT /api/user/medications/<med_id>`

🔒 **需認證**

更新用藥（部分更新）。請求格式同 POST，所有欄位皆為可選。若傳 `schedules` 則全部替換。

---

### `DELETE /api/user/medications/<med_id>`

🔒 **需認證**

刪除用藥紀錄。

**回應 200：**
```json
{
  "success": true,
  "message": "用藥紀錄已刪除"
}
```

---

## 服藥紀錄 Adherence

### `POST /api/user/adherence`

🔒 **需認證**

記錄服藥行為。

**請求：**
```json
{
  "medication_id": 1,
  "status": "taken",
  "schedule_id": 1,
  "scheduled_date": "2026-05-27",
  "note": ""
}
```

| 欄位 | 類型 | 必填 | 說明 |
|---|---|---|---|
| medication_id | integer | ✅ | 用藥 ID |
| status | string | ✅ | `taken` / `skipped` / `late` |
| schedule_id | integer | ❌ | 排程 ID |
| scheduled_date | string | ❌ | YYYY-MM-DD（預設今天） |
| note | string | ❌ | 備註 |

> 當 `status=taken` 且該藥有 `stock_qty` 時，庫存自動 -1。

**回應 201：**
```json
{
  "success": true,
  "log": {
    "id": 1,
    "user_id": 1,
    "medication_id": 1,
    "schedule_id": 1,
    "status": "taken",
    "taken_at": "2026-05-27T10:00:00",
    "scheduled_date": "2026-05-27",
    "note": ""
  }
}
```

---

### `GET /api/user/adherence`

🔒 **需認證**

查詢服藥紀錄（依日期範圍）。

**Query 參數：**
| 參數 | 類型 | 說明 |
|---|---|---|
| medication_id | integer | 篩選特定用藥 |
| start | string | 起始日期 YYYY-MM-DD |
| end | string | 結束日期 YYYY-MM-DD |

---

### `GET /api/user/adherence/stats`

🔒 **需認證**

取得服藥統計（遵從率）。

**Query 參數：**
| 參數 | 類型 | 說明 |
|---|---|---|
| days | integer | 統計近 N 天（預設 30） |

**回應 200：**
```json
{
  "success": true,
  "stats": {
    "days": 30,
    "total": 60,
    "taken": 55,
    "skipped": 3,
    "late": 2,
    "adherence_rate": 91.7
  }
}
```

---

## Push Token 管理

### `POST /api/user/push-token`

🔒 **需認證**

註冊推播 Token。

**請求：**
```json
{
  "token": "device-push-token-string",
  "platform": "ios"
}
```

| 欄位 | 類型 | 必填 | 說明 |
|---|---|---|---|
| token | string | ✅ | 裝置推播 Token |
| platform | string | ✅ | `ios` / `android` / `web` |

**回應 200：**
```json
{
  "success": true,
  "message": "Push token 已註冊"
}
```

---

### `DELETE /api/user/push-token`

🔒 **需認證**

取消推播 Token。

**請求：**
```json
{
  "token": "device-push-token-string"
}
```

**回應 200：**
```json
{
  "success": true,
  "message": "Push token 已取消"
}
```

---

## 安全檢查 Safety

### `POST /api/safety/check`

🔒 **需認證**

對指定藥物執行 4 層安全檢查（過敏 → 重複用藥 → 交互作用 → 分級）。

**請求：**
```json
{
  "drug_id": 123,
  "profile_id": 1
}
```

| 欄位 | 類型 | 必填 | 說明 |
|---|---|---|---|
| drug_id | integer | ✅ | 藥物 ID |
| profile_id | integer | ❌ | 指定成員（未指定則檢查全部） |

**回應 200：**
```json
{
  "success": true,
  "overall": "safe",
  "checks": [
    {
      "type": "allergy",
      "status": "pass",
      "details": []
    },
    {
      "type": "duplicate",
      "status": "pass",
      "details": []
    },
    {
      "type": "interaction",
      "status": "pass",
      "details": []
    },
    {
      "type": "grading",
      "status": "pass",
      "details": []
    }
  ]
}
```

| overall 值 | 說明 |
|---|---|
| `safe` | 所有檢查通過 |
| `warning` | 有中度風險 |
| `danger` | 有嚴重風險 |

---

### `GET /api/safety/interactions`

🔒 **需認證**

查詢藥物交互作用。

**Query 參數：**
| 參數 | 類型 | 說明 |
|---|---|---|
| ingredient | string | 成分名稱（模糊搜尋） |
| severity | string | `mild` / `moderate` / `severe` |
| page | integer | 頁碼（預設 1） |
| per_page | integer | 每頁筆數（預設 20） |

**回應 200：**
```json
{
  "success": true,
  "interactions": [
    {
      "id": 1,
      "ingredient_a": "乙醯胺酚",
      "ingredient_b": "Warfarin",
      "severity": "moderate",
      "description": "可能增強抗凝血效果",
      "recommendation": "需醫師監控"
    }
  ],
  "total": 12,
  "page": 1,
  "per_page": 20
}
```

---

### `GET /api/safety/allergies`

🔒 **需認證**

列出使用者的過敏紀錄。

**回應 200：**
```json
{
  "success": true,
  "allergies": [
    {
      "id": 1,
      "user_id": 1,
      "ingredient_id": 1,
      "ingredient_name": "乙醯胺酚",
      "severity": "severe",
      "note": "服用後會起紅疹",
      "created_at": "2026-05-27T10:00:00"
    }
  ]
}
```

---

### `POST /api/safety/allergies`

🔒 **需認證**

新增過敏紀錄。

**請求：**
```json
{
  "ingredient_id": 1,
  "severity": "severe",
  "note": "服用後會起紅疹"
}
```

| 欄位 | 類型 | 必填 | 說明 |
|---|---|---|---|
| ingredient_id | integer | ✅ | 成分 ID |
| severity | string | ❌ | `mild` / `moderate`（預設）/ `severe` |
| note | string | ❌ | 備註 |

**回應 201：**
```json
{
  "success": true,
  "allergy": { ... }
}
```

**錯誤：**
| 狀態碼 | 情境 |
|---|---|
| 404 | 成分不存在 |
| 409 | 已記錄此過敏成分 |

---

### `DELETE /api/safety/allergies/<allergy_id>`

🔒 **需認證**

刪除過敏紀錄。

**回應 200：**
```json
{
  "success": true,
  "message": "已刪除"
}
```

---

## 錯誤碼對照

所有錯誤回應格式一致：

```json
{
  "success": false,
  "error": "錯誤描述"
}
```

| HTTP 狀態碼 | 說明 |
|---|---|
| 400 | 請求格式錯誤 / 參數不合法 |
| 401 | 未認證 / Token 過期 |
| 403 | 帳號已停用 |
| 404 | 資源不存在 |
| 405 | 不允許的 HTTP 方法 |
| 409 | 資源衝突（重複） |
| 413 | 檔案過大 |
| 429 | 請求過於頻繁 |
| 500 | 伺服器內部錯誤 |
| 503 | 服務暫不可用 |
