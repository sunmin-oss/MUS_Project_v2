# Feature Spec 06：安全性功能

> 狀態：規劃中（Draft）
> 分類：安全性功能
> 對應變現：基本警示免費；進階分析付費（見 spec 05）
> ⭐ **App 核心差異化價值**

---

## 1. 功能總覽

在使用者新增藥品、辨識藥品、匯入處方箋、或服藥前，自動進行多項安全檢查，及早發現風險。

包含子功能：
1. 交互作用警示（Drug-Drug Interaction）
2. 重複用藥檢測（Duplicate Therapy Detection）
3. 過敏警示（Allergy Alert）
4. 用藥安全分級提示（Safety Category for Special Populations）

---

## 2. 目標使用者

- 多科別就醫、用藥複雜的患者
- 慢性病患者（多項長期用藥）
- 孕婦、哺乳婦、兒童、長者
- 有藥物過敏史的使用者
- 自行購買 OTC 與保健品的使用者

---

## 3. 使用者故事

- US-6.1：身為使用者，當我新增一種藥，App 自動檢查與我目前用藥是否衝突。
- US-6.2：身為使用者，當我加入兩種含相同成分的藥（如普拿疼 + 感冒藥），App 警告我重複用藥。
- US-6.3：身為使用者，App 在我新增的藥含有我過敏成分時立即阻擋並警告。
- US-6.4：身為孕婦，當我辨識藥品時，App 顯示「此藥孕婦用藥分級為 C，建議諮詢醫師」。
- US-6.5：身為照顧者，當我幫父母新增藥品，App 自動套用「長者用藥」的較嚴格檢查。

---

## 4. 子功能規格

### 4.1 交互作用警示

**檢查時機**：
- 新增藥品時
- 處方箋 OCR 匯入時
- 辨識藥品後加入用藥清單時
- 定期掃描（每週對現有用藥清單檢查一次）

**警示等級**：
| 等級 | 顏色 | 行為 |
|---|---|---|
| 🟥 嚴重（Contraindicated） | 紅 | 強制顯示 modal，需使用者明確確認 |
| 🟧 高風險（Major） | 橘 | 顯示警示橫幅，提示諮詢藥師 |
| 🟨 中度（Moderate） | 黃 | 顯示警示但可直接繼續 |
| 🟦 輕度（Minor） | 藍 | 僅作 info 提示 |

**警示內容應包含**：
- 涉及的藥品名稱（雙方）
- 風險描述（簡短、白話）
- 可能後果
- 建議行動（諮詢醫師/錯開時間/避免併用）
- 風險來源（資料庫引用）

**免費 vs 付費**：
- 免費：🟥 + 🟧 全顯示
- 付費：上述 + 🟨 + 🟦 + **詳細機轉說明、學術引用**

### 4.2 重複用藥檢測

**檢測邏輯**：
- 以「成分（active ingredient）」為比對基礎，而非商品名
- 範例：普拿疼 (Acetaminophen) + 普拿疼伏冒 (Acetaminophen + Pseudoephedrine) → 重複
- 跨類別比對：處方藥 + OTC + 保健品都納入

**警示內容**：
- 重複的成分名稱
- 兩種藥品總劑量
- 是否超過建議上限（如：Acetaminophen 每日 ≤ 4g）
- 建議：保留哪一種、停用哪一種

**免費 vs 付費**：
- 免費：處方藥之間的重複檢測
- 付費：含 OTC + 保健品的全面比對

### 4.3 過敏警示

**過敏資料來源**：
- 使用者主動建立過敏清單（成分名/藥品名）
- 從處方箋 OCR 結果中標註過敏（醫師欄位）
- 「藥物不良反應」回報自動建議加入過敏清單

**檢查時機**：
- 任何新增藥品的時刻
- 辨識結果顯示前（防止使用者誤用）

**警示行為**：
- 🚨 強制阻擋：偵測到過敏成分時，必須使用者明確按「我了解風險仍要繼續」才能加入
- 自動填寫「諮詢藥師」按鈕

**進階**：
- 交叉過敏警示（如：對 Penicillin 過敏 → 對 Cephalosporin 也警示）

### 4.4 用藥安全分級提示

**支援族群**：
| 族群 | 分級標準 |
|---|---|
| 孕婦 | FDA Pregnancy Category（A/B/C/D/X）|
| 哺乳婦 | LactMed 風險分級 |
| 兒童 | 依年齡段標示（新生兒/嬰兒/兒童）|
| 長者 | Beers Criteria（老年人潛在不適當用藥）|
| 肝/腎功能不全 | 標示需減量或避免 |

**顯示時機**：
- Profile 設定相關屬性（懷孕中、哺乳中、年齡、慢性病等）
- 該 Profile 新增或辨識藥品時自動套用相應檢查

**免費 vs 付費**：
- 免費：基本分級顯示（孕婦 C 級、長者警示等）
- 付費：詳細風險評估報告（綜合多項條件、替代藥建議）

---

## 5. 資料模型（草案）

```
DrugInteraction
 ├─ drug_a_id, drug_b_id
 ├─ severity (contraindicated/major/moderate/minor)
 ├─ description, mechanism, recommendation
 └─ source_reference

DrugIngredient
 ├─ drug_id, ingredient_id
 └─ amount, unit

UserAllergy
 ├─ profile_id, ingredient_id (or free_text)
 ├─ severity, reaction_description
 └─ verified_by (self/doctor/ocr)

DrugSafetyProfile
 ├─ drug_id
 ├─ pregnancy_category, lactation_risk
 ├─ pediatric_safety, geriatric_safety (beers)
 ├─ hepatic_adjustment, renal_adjustment
 └─ source_reference

SafetyCheckLog (稽核用)
 ├─ profile_id, triggered_at
 ├─ check_type, result
 └─ user_action (acknowledged/ignored/consulted)
```

---

## 6. 資料來源

| 資料 | 來源候選 |
|---|---|
| 交互作用 | DrugBank / FDA Drug Interactions / DDInter / 衛福部仿單 |
| 成分 | 衛福部食藥署藥品許可證資料庫 / 仿單 |
| 孕婦分級 | FDA / Australian Pregnancy Risk |
| 長者用藥 | Beers Criteria 2023 |
| Beers/老年用藥 | American Geriatrics Society |

> ⚠️ 資料授權須逐一確認，部分為商業授權。

---

## 7. 變現分層（摘要，詳見 spec 05）

| 功能 | 免費 | 付費 |
|---|---|---|
| 過敏警示 | ✅ 完整 | ✅ 完整 |
| 重複用藥（處方藥） | ✅ | ✅ |
| 重複用藥（含 OTC/保健品）| ❌ | ✅ |
| 交互作用（嚴重/高風險）| ✅ | ✅ |
| 交互作用（中/低風險 + 機轉）| ❌ | ✅ |
| 安全分級（基本標示）| ✅ | ✅ |
| 個人化風險報告 | ❌ | ✅ |

---

## 8. 技術考量

- **效能**：警示計算須在 < 500ms 完成（不能讓使用者等）
- **快取**：使用者用藥清單變更時預先計算所有 pair 的交互作用
- **離線**：核心安全規則應可離線運作（不依賴網路）
- **更新**：交互作用資料庫定期更新（每季）
- **多語**：警示文字須繁中/英文

---

## 9. 風險

- **資料完整性**：資料庫不全可能造成「漏警示」，比「誤警示」更嚴重
- **過度警示疲乏**：警示太多使用者會無視（建議分級設計）
- **法規責任**：警示不可使用「請停藥」「請改用 X」等明確醫囑用語
- **個資**：過敏史、疾病史屬敏感資料，須加密存放

---

## 10. 驗收條件（DoD）

- [ ] 新增藥品時自動觸發 4 項檢查
- [ ] 警示分級正確顯示（顏色 / 行為差異）
- [ ] 過敏警示能阻擋使用者誤加藥品
- [ ] 重複用藥能跨處方/OTC/保健品比對
- [ ] 孕婦/長者 Profile 套用對應分級
- [ ] 所有檢查行為紀錄在 SafetyCheckLog（稽核可追溯）
- [ ] 警示計算延遲 < 500ms

---

## 11. 未決議題

- [ ] 採用哪個交互作用資料庫？（涉及授權成本）
- [ ] 是否實作「藥物不良反應主動回報」並貢獻回資料庫？
- [ ] 警示通知是否要推送（背景定期掃描）？
- [ ] 過敏警示誤判導致使用者無法加藥，是否提供 override 流程與紀錄？
