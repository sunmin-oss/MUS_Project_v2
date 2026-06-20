# 程式碼片段 1：RAG 辨識核心提示詞 (vision_api_gemini.py)
# 用途：論文 3.3 節 — RAG 檢索增強生成辨識技術

def recognize_with_rag(self, image_path, drug_database=None):
    """使用 RAG (檢索增強生成) 方式識別藥物"""
    # 從資料庫取得藥物特徵清單（500 筆）
    drug_features = drug_database.get_drug_features_for_rag(sample_size=500)

    # RAG 核心提示詞 — 讓 AI 從真實藥物庫中選擇
    prompt = f"""你是藥物識別專家。分析照片中的藥物，
    從下方藥物庫選擇最匹配的藥物。

    【規則】
    - 必須從藥物庫中選擇，不能自創藥物名稱
    - 優先比對刻印標記（最重要）、再比對顏色和形狀

    【藥物庫格式】每行: ID|刻印標記(正面/背面)|中文名|形狀|顏色
    {drug_features}

    【任務】
    1. 描述照片中藥物的刻印文字、顏色、形狀
    2. 從藥物庫找出 3-5 個最匹配的藥物
    3. 回傳 JSON"""

    # 發送圖片 + 提示詞到 Gemini API
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": mime_type, "data": image_b64}}
            ]
        }]
    }
