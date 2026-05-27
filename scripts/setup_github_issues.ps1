# ======================================================================
# GitHub Issues / Milestones / Labels 一次性建立腳本
# 對應：docs/SPRINT_PLAN.md
# 用法：
#   1. 先確認已安裝 GitHub CLI：gh --version
#   2. 登入：gh auth login
#   3. 執行：./scripts/setup_github_issues.ps1
#   重複執行安全：已存在的 label/milestone/issue 會被略過（issue 會以標題比對）
# ======================================================================

$ErrorActionPreference = "Continue"
$Repo = "sunmin-oss/MUS_Project_v2"

# ----------------------------------------------------------------------
# 1. Labels
# ----------------------------------------------------------------------
Write-Host "`n=== 建立 Labels ===" -ForegroundColor Cyan

$Labels = @(
    @{ name = "sprint-1";          color = "0e8a16"; desc = "Sprint 1 (5/27-6/2) 基礎 + 爬蟲" },
    @{ name = "sprint-2";          color = "0e8a16"; desc = "Sprint 2 (6/3-6/9) Auth 完備" },
    @{ name = "sprint-3";          color = "0e8a16"; desc = "Sprint 3 (6/10-6/16) Medications + Safety" },
    @{ name = "sprint-4";          color = "0e8a16"; desc = "Sprint 4 (6/17-6/23) 推播 + 整合" },
    @{ name = "sprint-5";          color = "0e8a16"; desc = "Sprint 5 (6/24-6/30) 穩定化 + Demo" },
    @{ name = "module:auth";       color = "1d76db"; desc = "使用者認證 / JWT / Profile" },
    @{ name = "module:crawler";    color = "1d76db"; desc = "NHI/TFDA 爬蟲與資料更新" },
    @{ name = "module:safety";     color = "1d76db"; desc = "安全性檢查（過敏/交互/分級）" },
    @{ name = "module:medications";color = "1d76db"; desc = "個人用藥管理" },
    @{ name = "module:push";       color = "1d76db"; desc = "推播通知（APNs/排程）" },
    @{ name = "module:infra";      color = "1d76db"; desc = "基礎建設 / ORM / 測試 / 部署" },
    @{ name = "priority:P0";       color = "b60205"; desc = "必須完成（MVP 阻擋）" },
    @{ name = "priority:P1";       color = "d93f0b"; desc = "重要但可微調" },
    @{ name = "priority:P2";       color = "fbca04"; desc = "次要 / 可延後" }
)

foreach ($l in $Labels) {
    gh label create $l.name --color $l.color --description $l.desc --repo $Repo 2>$null
    if ($LASTEXITCODE -eq 0) { Write-Host "  + $($l.name)" -ForegroundColor Green }
    else { Write-Host "  · $($l.name) (已存在)" -ForegroundColor DarkGray }
}

# ----------------------------------------------------------------------
# 2. Milestones
# ----------------------------------------------------------------------
Write-Host "`n=== 建立 Milestones ===" -ForegroundColor Cyan

$Milestones = @(
    @{ title = "Sprint 1 - 6/2";  due = "2026-06-02T23:59:59Z"; desc = "基礎建設 + 爬蟲加速（Quick Win）" },
    @{ title = "Sprint 2 - 6/9";  due = "2026-06-09T23:59:59Z"; desc = "⚠️ Auth API 必須完成（App W3 依賴）" },
    @{ title = "Sprint 3 - 6/16"; due = "2026-06-16T23:59:59Z"; desc = "⚠️ Medications + Safety API（App W3 依賴）" },
    @{ title = "Sprint 4 - 6/23"; due = "2026-06-23T23:59:59Z"; desc = "⚠️ 推播 + 整合（App W4 依賴）" },
    @{ title = "Sprint 5 - 6/30"; due = "2026-06-30T23:59:59Z"; desc = "穩定化 + Demo + Release v3.0.0" }
)

# 取得已存在的 milestones（避免重複建立）
$existing = gh api "repos/$Repo/milestones?state=all" --jq '.[].title' 2>$null

foreach ($m in $Milestones) {
    if ($existing -contains $m.title) {
        Write-Host "  · $($m.title) (已存在)" -ForegroundColor DarkGray
    } else {
        gh api "repos/$Repo/milestones" -f title="$($m.title)" -f due_on="$($m.due)" -f description="$($m.desc)" | Out-Null
        if ($LASTEXITCODE -eq 0) { Write-Host "  + $($m.title)" -ForegroundColor Green }
        else { Write-Host "  ✗ $($m.title) 建立失敗" -ForegroundColor Red }
    }
}

# ----------------------------------------------------------------------
# 3. Issues
# ----------------------------------------------------------------------
Write-Host "`n=== 建立 Issues ===" -ForegroundColor Cyan

# 共用 issue body 模板
function Make-Body($id, $sprint, $desc, $dod) {
    @"
**Task ID**: $id
**Sprint**: $sprint
**參考**: [docs/SPRINT_PLAN.md](../blob/develop/docs/SPRINT_PLAN.md) / [docs/BACKEND_ROADMAP.md](../blob/develop/docs/BACKEND_ROADMAP.md)

## 描述
$desc

## 完成條件 (DoD)
$dod
- [ ] 程式碼合到 develop（PR 通過 review）
- [ ] 對應 pytest 單元測試 ≥ 1 條
- [ ] 以 curl/Postman 實際呼叫成功
"@
}

# 取得已存在 issues 標題
$existingIssues = gh issue list --repo $Repo --state all --limit 200 --json title --jq '.[].title' 2>$null

$Issues = @(
    # ---------- Sprint 1 ----------
    @{ id="P0-1"; sprint="Sprint 1 - 6/2"; labels=@("sprint-1","module:infra","priority:P0");
       title="[P0-1] 引入 SQLAlchemy ORM 包裝既有 4 張表";
       desc="將 drugs/drug_images/nhi_cache/api_logs 改用 SQLAlchemy Model 操作，保留原 SQLite。";
       dod="- [ ] Models 定義完成`n- [ ] 既有查詢全部改寫`n- [ ] 不破壞現有 API 行為" },

    @{ id="P0-3"; sprint="Sprint 1 - 6/2"; labels=@("sprint-1","module:infra","priority:P0");
       title="[P0-3] Blueprint 模組化（/auth、/user、/safety）";
       desc="將 main.py 路由依模組拆分為獨立 Blueprint。";
       dod="- [ ] auth_routes.py / user_routes.py / safety_routes.py 建立`n- [ ] main.py 註冊各 Blueprint`n- [ ] 既有 /api/* 路徑不變" },

    @{ id="A1-1"; sprint="Sprint 1 - 6/2"; labels=@("sprint-1","module:auth","priority:P0");
       title="[A1-1] users / profiles 資料表 + ORM Model";
       desc="建立使用者與成員 schema，含 email、password_hash、subscription_tier、profiles 一對多。";
       dod="- [ ] Migration 腳本`n- [ ] User / Profile Model" },

    @{ id="A1-2"; sprint="Sprint 1 - 6/2"; labels=@("sprint-1","module:auth","priority:P0");
       title="[A1-2] bcrypt 密碼雜湊 + POST /api/auth/register";
       desc="使用 bcrypt 雜湊密碼，註冊端點驗證 email 格式與密碼強度。";
       dod="- [ ] /api/auth/register 端點`n- [ ] 重複 email 回 409`n- [ ] 密碼至少 8 碼" },

    @{ id="P0-4"; sprint="Sprint 1 - 6/2"; labels=@("sprint-1","module:infra","priority:P1");
       title="[P0-4] pytest 測試框架 + fixtures";
       desc="建立 tests/ 結構、conftest.py，含臨時 DB fixture 與測試 client。";
       dod="- [ ] tests/conftest.py`n- [ ] 範例測試 1 條可跑" },

    @{ id="A3-1"; sprint="Sprint 1 - 6/2"; labels=@("sprint-1","module:crawler","priority:P0");
       title="[A3-1] 爬蟲重構：Browser 實例由外部注入";
       desc="scripts/nhi_crawler.py 不再每次 p.chromium.launch()，改由 batch_update 注入共用 browser。";
       dod="- [ ] scrape_nhi_drug_info(browser, ...) 簽名`n- [ ] batch_update 維護生命週期" },

    @{ id="A3-2"; sprint="Sprint 1 - 6/2"; labels=@("sprint-1","module:crawler","priority:P0");
       title="[A3-2] 移除所有 wait_for_timeout 硬等";
       desc="改用 wait_for_selector / wait_for_load_state('networkidle')。";
       dod="- [ ] 3 處 timeout 全部替換`n- [ ] 仍能穩定爬完一筆" },

    @{ id="A3-3"; sprint="Sprint 1 - 6/2"; labels=@("sprint-1","module:crawler","priority:P1");
       title="[A3-3] 移除 tfda_detail_page_debug.txt 寫檔";
       desc="改成只在 DEBUG=True 才寫。";
       dod="- [ ] 環境變數控制" },

    @{ id="A3-4"; sprint="Sprint 1 - 6/2"; labels=@("sprint-1","module:crawler","priority:P0");
       title="[A3-4] 預設 delay=0.5s + 失敗指數退避";
       desc="成功路徑 0.5s，失敗時 1s → 2s → 4s（最多 3 次重試）。";
       dod="- [ ] config 化參數`n- [ ] 重試邏輯有單元測試" },

    @{ id="A3-5"; sprint="Sprint 1 - 6/2"; labels=@("sprint-1","module:crawler","priority:P1");
       title="[A3-5] DB 連線共用 + PRAGMA journal_mode=WAL";
       desc="batch_update 用單一長連線，啟用 WAL 提升並發寫效能。";
       dod="- [ ] 不再每筆 connect/close`n- [ ] 啟用 WAL" },

    @{ id="A3-7"; sprint="Sprint 1 - 6/2"; labels=@("sprint-1","module:crawler","priority:P1");
       title="[A3-7] 全表 benchmark：驗證 ≤ 1.5 小時";
       desc="跑一次全量更新並記錄實際耗時與每分鐘 throughput。";
       dod="- [ ] benchmark 報告（log / screenshot）`n- [ ] 達成 ≤ 1.5hr，未達需開後續 issue" },

    # ---------- Sprint 2 ----------
    @{ id="A1-3"; sprint="Sprint 2 - 6/9"; labels=@("sprint-2","module:auth","priority:P0");
       title="[A1-3] JWT Access Token + Refresh Token";
       desc="flask-jwt-extended：Access 15min、Refresh 7day。";
       dod="- [ ] /api/auth/login / /refresh / /logout 端點`n- [ ] Refresh 黑名單（redis 或記憶體）" },

    @{ id="A1-4"; sprint="Sprint 2 - 6/9"; labels=@("sprint-2","module:auth","priority:P0");
       title="[A1-4] @jwt_required 中介層 + current_user helper";
       desc="統一注入當前使用者，未驗證統一回 401。";
       dod="- [ ] decorator 可用`n- [ ] 錯誤格式統一" },

    @{ id="A1-8"; sprint="Sprint 2 - 6/9"; labels=@("sprint-2","module:auth","priority:P0");
       title="[A1-8] Profile CRUD（多人成員）";
       desc="/api/user/profiles GET/POST/PUT/DELETE。";
       dod="- [ ] is_primary 不可刪除`n- [ ] 跨 user 隔離" },

    @{ id="A1-9"; sprint="Sprint 2 - 6/9"; labels=@("sprint-2","module:auth","priority:P1");
       title="[A1-9] /api/recognize 加入可選 JWT + 紀錄歷史";
       desc="登入用戶記入 recognition_history，未登入仍可用但計匿名額度（額度延後 Phase 2）。";
       dod="- [ ] recognition_history 表`n- [ ] 端點維持向後相容" },

    @{ id="P0-5"; sprint="Sprint 2 - 6/9"; labels=@("sprint-2","module:infra","priority:P1");
       title="[P0-5] Rate Limit + Global Error Handler 中介層";
       desc="flask-limiter；統一 JSON 錯誤格式。";
       dod="- [ ] /api/auth/login 限制 5/min`n- [ ] 5xx 不洩漏 traceback" },

    @{ id="S6-1"; sprint="Sprint 2 - 6/9"; labels=@("sprint-2","module:safety","priority:P0");
       title="[S6-1] ingredients + drug_ingredients schema";
       desc="建立成分主表與藥品-成分對應表，補建既有 drugs 的對應資料（先空白可後續填）。";
       dod="- [ ] schema migration`n- [ ] 至少 demo 用 ≥10 種成分" },

    @{ id="S6-3"; sprint="Sprint 2 - 6/9"; labels=@("sprint-2","module:safety","priority:P0");
       title="[S6-3] user_allergies schema + CRUD";
       desc="使用者過敏紀錄，依 profile_id 隔離。";
       dod="- [ ] /api/user/allergies CRUD" },

    @{ id="S6-4"; sprint="Sprint 2 - 6/9"; labels=@("sprint-2","module:safety","priority:P1");
       title="[S6-4] drug_safety_profiles schema";
       desc="懷孕分級 / 哺乳 / 兒童 / 老年 / 肝腎調整。";
       dod="- [ ] schema migration" },

    @{ id="S6-5"; sprint="Sprint 2 - 6/9"; labels=@("sprint-2","module:safety","priority:P1");
       title="[S6-5] safety_check_logs schema";
       desc="所有安全檢查的稽核紀錄。";
       dod="- [ ] schema migration" },

    @{ id="A3-6"; sprint="Sprint 2 - 6/9"; labels=@("sprint-2","module:crawler","priority:P2");
       title="[A3-6] Admin batch update 端點補 throughput 指標";
       desc="回傳每分鐘處理筆數，前端儀表板可顯示。";
       dod="- [ ] /admin/api/batch-update/status 補欄位" },

    # ---------- Sprint 3 ----------
    @{ id="S1-1"; sprint="Sprint 3 - 6/16"; labels=@("sprint-3","module:medications","priority:P0");
       title="[S1-1] medications + medication_schedules CRUD";
       desc="個人用藥清單與排程（含 daily/weekly/custom）。";
       dod="- [ ] /api/user/medications CRUD`n- [ ] /schedules 子資源" },

    @{ id="S1-2"; sprint="Sprint 3 - 6/16"; labels=@("sprint-3","module:push","priority:P0");
       title="[S1-2] push_tokens schema + 註冊端點";
       desc="儲存 APNs token（per user/device）。";
       dod="- [ ] POST /api/user/push-token`n- [ ] 同 token 去重" },

    @{ id="S1-7"; sprint="Sprint 3 - 6/16"; labels=@("sprint-3","module:medications","priority:P0");
       title="[S1-7] adherence_logs + 日曆/統計端點";
       desc="服藥紀錄與順從率計算。";
       dod="- [ ] /api/user/adherence GET/POST/PUT`n- [ ] /stats 計算 N 天內順從率" },

    @{ id="S6-6"; sprint="Sprint 3 - 6/16"; labels=@("sprint-3","module:safety","priority:P0");
       title="[S6-6] SafetyCheckService 四層邏輯";
       desc="過敏 → 重複用藥 → 交互作用 → 安全分級。";
       dod="- [ ] check_all(profile_id, new_drug_id) 介面`n- [ ] 結果統一格式" },

    @{ id="S6-7"; sprint="Sprint 3 - 6/16"; labels=@("sprint-3","module:safety","priority:P0");
       title="[S6-7] /api/safety/check + /api/safety/interactions";
       desc="主動安全檢查 + 交互查詢端點。";
       dod="- [ ] 兩端點完成`n- [ ] 寫入 safety_check_logs" },

    @{ id="S6-2"; sprint="Sprint 3 - 6/16"; labels=@("sprint-3","module:safety","priority:P1");
       title="[S6-2] drug_interactions 表 + 手寫 demo 資料 ≥10 筆";
       desc="競賽 demo 用，先手動寫入常見高危組合（如 warfarin + aspirin）。";
       dod="- [ ] schema`n- [ ] ≥10 筆種子資料" },

    # ---------- Sprint 4 ----------
    @{ id="S1-3"; sprint="Sprint 4 - 6/23"; labels=@("sprint-4","module:push","priority:P0");
       title="[S1-3] APScheduler 單機整合";
       desc="背景排程器，每分鐘檢查到期提醒。";
       dod="- [ ] 啟動時自動載入`n- [ ] 任務可暫停/恢復" },

    @{ id="S1-5"; sprint="Sprint 4 - 6/23"; labels=@("sprint-4","module:push","priority:P0");
       title="[S1-5] APNs iOS 推播（p8 key 設定）";
       desc="aioapns 或 PyAPNs2 整合，HTTP/2 直連 Apple。";
       dod="- [ ] 實機收到測試推播`n- [ ] payload 含 deep link" },

    @{ id="S1-6"; sprint="Sprint 4 - 6/23"; labels=@("sprint-4","module:push","priority:P0");
       title="[S1-6] 排程掃描 → 觸發推播任務";
       desc="掃 medication_schedules + push_tokens，發送對應通知。";
       dod="- [ ] 已送出狀態記錄`n- [ ] 失敗重試 1 次" },

    @{ id="S1-stock"; sprint="Sprint 4 - 6/23"; labels=@("sprint-4","module:medications","priority:P1");
       title="[S1-stock] 補藥提醒（庫存倒數）";
       desc="medications.current_stock 與每日用量計算剩餘天數，≤ N 天發推播。";
       dod="- [ ] PUT /api/user/medications/<id>/stock`n- [ ] 排程任務" },

    @{ id="S6-recog"; sprint="Sprint 4 - 6/23"; labels=@("sprint-4","module:safety","priority:P0");
       title="[S6-recog] /api/recognize 串接 SafetyCheckService";
       desc="若帶 profile_id 則辨識後自動執行安全檢查，回傳警示陣列。";
       dod="- [ ] 回應格式擴充" },

    @{ id="S6-8"; sprint="Sprint 4 - 6/23"; labels=@("sprint-4","module:safety","priority:P0");
       title="[S6-8] /api/drug/<id> 補充安全分級與交互作用摘要";
       desc="高危等級摘要直接帶在藥品詳情中。";
       dod="- [ ] 回應補欄位`n- [ ] 文件更新" },

    @{ id="E2E-med"; sprint="Sprint 4 - 6/23"; labels=@("sprint-4","module:infra","priority:P1");
       title="[E2E] 用藥 → 排程 → 推播 全鏈路 pytest";
       desc="端對端測試，模擬時間推進觸發推播。";
       dod="- [ ] 一條 e2e 測試通過" },

    @{ id="E2E-safety"; sprint="Sprint 4 - 6/23"; labels=@("sprint-4","module:infra","priority:P1");
       title="[E2E] 辨識 → 安全檢查 全鏈路 pytest";
       desc="模擬上傳已知過敏藥圖片，驗證警示回傳。";
       dod="- [ ] 一條 e2e 測試通過" },

    # ---------- Sprint 5 ----------
    @{ id="S5-doc";  sprint="Sprint 5 - 6/30"; labels=@("sprint-5","module:infra","priority:P0");
       title="[S5-doc] API 文件（OpenAPI / Postman collection）";
       desc="所有端點文件化，含 request/response 範例。";
       dod="- [ ] docs/API.md`n- [ ] Postman collection 匯出檔" },

    @{ id="S5-deploy"; sprint="Sprint 5 - 6/30"; labels=@("sprint-5","module:infra","priority:P0");
       title="[S5-deploy] Staging 部署（Docker + nginx）";
       desc="HTTPS + reverse proxy + gunicorn workers。";
       dod="- [ ] App 端能從外網存取`n- [ ] HTTPS 憑證" },

    @{ id="S5-demo"; sprint="Sprint 5 - 6/30"; labels=@("sprint-5","module:infra","priority:P0");
       title="[S5-demo] 與 App 端聯合 Demo 演練";
       desc="完整跑一遍 Demo 流程，記錄問題清單。";
       dod="- [ ] 演練紀錄`n- [ ] 修復 P0 bug" },

    @{ id="S5-release"; sprint="Sprint 5 - 6/30"; labels=@("sprint-5","module:infra","priority:P0");
       title="[S5-release] Release v3.0.0 Tag";
       desc="release/v3.0.0 流程：develop → release → main → tag → develop。";
       dod="- [ ] tag v3.0.0 推上 origin" },

    @{ id="S5-stress"; sprint="Sprint 5 - 6/30"; labels=@("sprint-5","module:infra","priority:P1");
       title="[S5-stress] 壓測 + Rate Limit 調校";
       desc="locust 或 ab 壓測辨識/搜尋端點，調整 worker / limit。";
       dod="- [ ] 報告：QPS / p95 延遲" },

    @{ id="S5-monitor"; sprint="Sprint 5 - 6/30"; labels=@("sprint-5","module:infra","priority:P2");
       title="[S5-monitor] 監控指標儀表板";
       desc="既有 api_logs 表延伸：每日請求數、錯誤率、平均延遲。";
       dod="- [ ] /admin 儀表板呈現" }
)

$created = 0; $skipped = 0; $failed = 0
foreach ($i in $Issues) {
    if ($existingIssues -contains $i.title) {
        Write-Host "  · $($i.title) (已存在)" -ForegroundColor DarkGray
        $skipped++
        continue
    }

    $body = Make-Body $i.id $i.sprint $i.desc $i.dod
    $labelArgs = $i.labels -join ","

    gh issue create --repo $Repo `
        --title $i.title `
        --body $body `
        --label $labelArgs `
        --milestone $i.sprint | Out-Null

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  + $($i.title)" -ForegroundColor Green
        $created++
    } else {
        Write-Host "  ✗ $($i.title) 建立失敗" -ForegroundColor Red
        $failed++
    }
}

Write-Host "`n=== 完成 ===" -ForegroundColor Cyan
Write-Host "  新增：$created" -ForegroundColor Green
Write-Host "  略過：$skipped" -ForegroundColor DarkGray
Write-Host "  失敗：$failed" -ForegroundColor Red
Write-Host "`n查看：https://github.com/$Repo/issues" -ForegroundColor Cyan
