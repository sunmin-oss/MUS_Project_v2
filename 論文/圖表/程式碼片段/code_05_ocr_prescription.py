# 程式碼片段 5：藥單 OCR 處方箋辨識 (vision_api_gemini.py)
# 用途：論文 3.4 節 — 處方箋 OCR 辨識技術

def recognize_prescription(self, image_path):
    """從藥單圖片中提取所有藥物名稱"""
    # 準備 OCR 專用提示詞
    prompt = """請分析這張醫院藥單/處方箋的照片。
    請提取出上面每一項藥物的以下資訊，回傳 JSON 陣列：
    - license_number: 許可證字號
    - chinese_name: 中文藥名
    - english_name: 英文藥名
    - route: 給藥途徑（口服/外用/注射等）
    - days: 天數（純數字）
    - frequency: 服用頻率（QD/BID/TID/QID 等）
    - dose_per_time: 每次劑量
    - total_quantity: 總量
    - ingredient: 成分名稱

    規則：
    1. 每一條藥物都要提取，不要遺漏
    2. 看不清楚的欄位填空字串 ""
    3. 只回傳 JSON"""

    # Gemini Vision API 呼叫
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": mime_type, "data": image_b64}}
            ]
        }]
    }
    response = requests.post(api_url, json=payload, headers=headers, timeout=30)

    # 解析回傳的 JSON 陣列
    parsed = json.loads(json_match.group())

    # 結構化資料儲存供後續比對
    if parsed and isinstance(parsed[0], dict):
        self._last_prescription_details = parsed
        names = []
        for item in parsed:
            name = item.get("chinese_name", "") or item.get("english_name", "")
            if name:
                names.append(name)
        return names
