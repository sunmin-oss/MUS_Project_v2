"""
==============================================
Google Gemini Vision API 包裝器
==============================================

【功能說明】
使用 Google Gemini Vision API 進行藥物圖片識別。
Gemini 是 Google 最強大的多模態 AI 模型，特別適合藥物辨識任務。

【API 文件】
https://ai.google.dev/

【優點】
- 支援高解析度圖片
- 更好的物體識別能力
- 支援中文指令
- 可以理解複雜場景

【作者】MUS2 團隊
【日期】2025
"""

import base64
import logging
from typing import List, Dict, Any
import json
from pathlib import Path
import requests

logger = logging.getLogger(__name__)


class GeminiVisionRecognizer:
    """Google Gemini Vision API 藥物識別器 (使用 REST API)"""

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        """
        初始化 Gemini Vision 識別器

        參數:
            api_key: Google Generative AI API 密鑰
        """
        if not api_key:
            raise ValueError("Gemini API 密鑰未提供")

        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.model_name = model_name

        logger.info("✓ Google Gemini Vision API 識別器已初始化")

    def recognize(self, image_path: str) -> List[Dict[str, Any]]:
        """
        識別圖片中的藥物

        參數:
            image_path: 圖片檔案路徑

        回傳:
            [{
                'name': '藥物名稱',
                'confidence': 0.95,
                'description': '描述'
            }, ...]
        """
        try:
            # 讀取圖片
            image_file = Path(image_path)
            if not image_file.exists():
                raise FileNotFoundError(f"圖片檔案不存在: {image_path}")

            # 讀取圖片數據
            with open(image_file, "rb") as f:
                image_data = f.read()

            # 判斷 MIME 類型
            suffix = image_file.suffix.lower()
            mime_type_map = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }
            mime_type = mime_type_map.get(suffix, "image/jpeg")

            # 編碼為 base64
            image_b64 = base64.standard_b64encode(image_data).decode("utf-8")

            # 準備提示詞
            prompt = """請分析這張圖片中的藥物。回答以下問題：

1. 圖片中是否有藥物？(是/否)
2. 如果有藥物，請識別：
   - 藥物名稱（中文或英文）
   - 藥物形狀（例如：圓形、橢圓形、長方形）
   - 藥物顏色（例如：白色、紅色、黃色）
   - 任何可見的刻印或標記
   - 你的識別信心度（0-1之間）

請回傳 JSON 格式的結果，格式如下：
{
    "has_medicine": true/false,
    "medicines": [
        {
            "name": "藥物名稱",
            "shape": "形狀",
            "color": "顏色",
            "markings": "刻印標記",
            "confidence": 0.85,
            "description": "簡短描述"
        }
    ],
    "additional_info": "任何其他相關信息"
}

只回傳 JSON，不需要其他文字。"""

            # 調用 Gemini API (REST API v1beta)
            logger.info(f"📤 發送圖片到 Gemini API: {image_path} (類型: {mime_type})")

            # 構建 API URL
            api_url = (
                f"{self.base_url}/{self.model_name}:generateContent?key={self.api_key}"
            )

            # 構建請求體
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": image_b64,
                                }
                            },
                        ]
                    }
                ]
            }

            # 發送請求
            headers = {"Content-Type": "application/json"}

            response = requests.post(api_url, json=payload, headers=headers, timeout=30)

            logger.info(f"📥 Gemini API 回應狀態碼: {response.status_code}")

            # 檢查是否成功
            if response.status_code != 200:
                error_detail = response.text
                logger.error(
                    f"✗ Gemini API 錯誤 ({response.status_code}): {error_detail}"
                )
                raise Exception(
                    f"Gemini API 錯誤 (狀態碼 {response.status_code}): {error_detail}"
                )

            # 解析回應
            response_data = response.json()
            logger.info(f"✓ Gemini API 回應結構: {list(response_data.keys())}")

            # 提取文本內容
            if "candidates" not in response_data or not response_data["candidates"]:
                logger.warning("⚠️ Gemini 無候選回應")
                return []

            candidate = response_data["candidates"][0]
            if "content" not in candidate or "parts" not in candidate["content"]:
                logger.warning("⚠️ Gemini 回應無內容部分")
                return []

            # 獲取文本回應（跳過 thinking parts）
            result_text = ""
            for part in candidate["content"]["parts"]:
                if part.get("thought"):
                    continue
                if "text" in part:
                    result_text = part["text"]
            if not result_text:
                for part in candidate["content"]["parts"]:
                    if "text" in part:
                        result_text = part["text"]

            logger.info(f"✓ Gemini 回應文本: {result_text[:100]}...")

            # 嘗試提取 JSON
            medicines = self._parse_json_response(result_text)

            logger.info(f"✓ Gemini 識別完成，找到 {len(medicines)} 個結果")
            return medicines

        except FileNotFoundError as e:
            logger.error(f"✗ 檔案錯誤: {e}")
            raise Exception(f"檔案錯誤: {str(e)}")
        except requests.exceptions.RequestException as e:
            logger.error(f"✗ 網路請求失敗: {e}")
            raise Exception(f"網路請求失敗: {str(e)}")
        except Exception as e:
            logger.error(f"✗ Gemini 識別失敗: {e}")
            import traceback

            logger.error(f"錯誤堆棧: {traceback.format_exc()}")
            raise Exception(f"Gemini Vision API 錯誤: {str(e)}")

    def _parse_json_response(self, response_text: str) -> List[Dict[str, Any]]:
        """解析 Gemini 的 JSON 回應"""
        medicines = []

        try:
            # 嘗試直接解析 JSON
            data = json.loads(response_text)
        except json.JSONDecodeError:
            # 如果直接解析失敗，嘗試提取 JSON 部分
            import re

            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                except json.JSONDecodeError:
                    logger.warning(f"⚠ 無法解析 Gemini 回應: {response_text}")
                    return []
            else:
                logger.warning(f"⚠ 無法找到 JSON 在回應中: {response_text}")
                return []

        # 檢查是否有藥物
        if not data.get("has_medicine", False):
            return []

        # 提取藥物資訊
        for medicine in data.get("medicines", [])[:10]:
            medicines.append(
                {
                    "name": medicine.get("name", "未知藥物"),
                    "confidence": medicine.get("confidence", 0.5),
                    "description": medicine.get("description", ""),
                    "shape": medicine.get("shape", ""),
                    "color": medicine.get("color", ""),
                    "markings": medicine.get("markings", ""),
                    "source": "gemini_vision",
                }
            )

        # 按信心度排序
        medicines.sort(key=lambda x: x["confidence"], reverse=True)

        return medicines[:10]  # 最多回傳 10 個結果

    def search_by_text(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        使用 Gemini 進行文字搜尋
        查詢藥物或取得相關建議

        參數:
            query: 搜尋關鍵字（藥物名稱、症狀等）
            limit: 最多回傳結果數

        回傳:
            [{
                'name': '藥物名稱',
                'confidence': 0.8,
                'description': '藥物描述',
                'source': 'gemini_search'
            }, ...]
        """
        try:
            # 準備搜尋提示詞
            prompt = f"""請幫我搜尋或推薦相關藥物。

搜尋關鍵字: {query}

請回傳最多 {limit} 個相關的藥物推薦，包括：
1. 藥物名稱（中文或英文）
2. 主要成分
3. 適用症狀
4. 你的推薦信心度（0-1之間）
5. 簡短描述

請回傳 JSON 格式的結果，格式如下：
{{
    "has_results": true/false,
    "medicines": [
        {{
            "name": "藥物名稱",
            "ingredient": "主要成分",
            "uses": "適用症狀",
            "confidence": 0.85,
            "description": "簡短描述"
        }}
    ],
    "note": "任何額外說明"
}}

只回傳 JSON，不需要其他文字。"""

            logger.info(f"🔍 使用 Gemini 搜尋: {query}")

            # 調用 Gemini 文字 API (REST API v1beta)
            api_url = (
                f"{self.base_url}/{self.model_name}:generateContent?key={self.api_key}"
            )

            payload = {"contents": [{"parts": [{"text": prompt}]}]}

            headers = {"Content-Type": "application/json"}

            response = requests.post(api_url, json=payload, headers=headers, timeout=30)

            logger.info(f"📥 Gemini 搜尋回應狀態碼: {response.status_code}")

            if response.status_code != 200:
                error_detail = response.text
                logger.error(
                    f"✗ Gemini 搜尋錯誤 ({response.status_code}): {error_detail}"
                )
                return []

            # 解析回應
            response_data = response.json()

            # 提取文本內容
            if "candidates" not in response_data or not response_data["candidates"]:
                logger.warning("⚠️ Gemini 無搜尋候選回應")
                return []

            candidate = response_data["candidates"][0]
            if "content" not in candidate or "parts" not in candidate["content"]:
                logger.warning("⚠️ Gemini 搜尋回應無內容部分")
                return []

            # 獲取文本回應（跳過 thinking parts）
            result_text = ""
            for part in candidate["content"]["parts"]:
                if part.get("thought"):
                    continue
                if "text" in part:
                    result_text = part["text"]
            if not result_text:
                for part in candidate["content"]["parts"]:
                    if "text" in part:
                        result_text = part["text"]

            logger.info(f"✓ Gemini 搜尋回應: {result_text[:100]}...")

            # 解析 JSON 回應
            medicines = self._parse_search_response(result_text)

            logger.info(f"✓ Gemini 搜尋完成，找到 {len(medicines)} 個結果")
            return medicines

        except Exception as e:
            logger.error(f"✗ Gemini 搜尋失敗: {e}")
            import traceback

            logger.error(f"錯誤堆棧: {traceback.format_exc()}")
            return []

    def _parse_search_response(self, response_text: str) -> List[Dict[str, Any]]:
        """解析 Gemini 搜尋的 JSON 回應"""
        medicines = []

        try:
            # 嘗試直接解析 JSON
            data = json.loads(response_text)
        except json.JSONDecodeError:
            # 如果直接解析失敗，嘗試提取 JSON 部分
            import re

            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                except json.JSONDecodeError:
                    logger.warning(f"⚠ 無法解析 Gemini 搜尋回應: {response_text}")
                    return []
            else:
                logger.warning(f"⚠ 無法找到 JSON 在搜尋回應中: {response_text}")
                return []

        # 檢查是否有結果
        if not data.get("has_results", False):
            return []

        # 提取藥物資訊
        for medicine in data.get("medicines", [])[:10]:
            medicines.append(
                {
                    "name": medicine.get("name", "未知藥物"),
                    "confidence": medicine.get("confidence", 0.5),
                    "description": medicine.get("description", ""),
                    "ingredient": medicine.get("ingredient", ""),
                    "uses": medicine.get("uses", ""),
                    "source": "gemini_search",
                }
            )

        # 按信心度排序
        medicines.sort(key=lambda x: x["confidence"], reverse=True)

        return medicines[:10]  # 最多回傳 10 個結果

    def recognize_with_rag(
        self, image_path: str, drug_database=None
    ) -> List[Dict[str, Any]]:
        """
        使用 RAG (檢索增強生成) 方式識別藥物

        這種方法將資料庫中的所有藥物作為上下文提供給 Gemini，
        讓 AI 從真實的藥物列表中選擇，而不是盲目猜測。
        這大幅提高了識別準確度。

        參數:
            image_path: 圖片檔案路徑
            drug_database: DrugDatabase 實例

        回傳:
            識別結果列表
        """
        try:
            if drug_database is None:
                logger.warning("⚠️ RAG 模式需要資料庫實例")
                return self.recognize(image_path)

            # 取得資料庫中的藥物特徵列表
            drug_features = drug_database.get_drug_features_for_rag(sample_size=500)

            if not drug_features:
                logger.warning("⚠️ 無法取得藥物特徵清單，回退到普通模式")
                return self.recognize(image_path)

            # 讀取圖片
            image_file = Path(image_path)
            if not image_file.exists():
                raise FileNotFoundError(f"圖片檔案不存在: {image_path}")

            with open(image_file, "rb") as f:
                image_data = f.read()

            suffix = image_file.suffix.lower()
            mime_type_map = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }
            mime_type = mime_type_map.get(suffix, "image/jpeg")
            image_b64 = base64.standard_b64encode(image_data).decode("utf-8")

            # 準備改進的提示詞 - 讓 AI 從資料庫中選擇
            prompt = f"""你是藥物識別專家。分析照片中的藥物，從下方藥物庫選擇最匹配的藥物。

【規則】
- 必須從藥物庫中選擇，不能自創藥物名稱
- 優先比對刻印標記（最重要）、再比對顏色和形狀
- 如果照片中能看到刻印文字（如 CCP、265 等），優先匹配標記完全一致的藥物

【藥物庫格式】每行: ID|刻印標記(正面/背面)|中文名|形狀|顏色
{drug_features}

【任務】
1. 描述照片中藥物的刻印文字、顏色、形狀
2. 從藥物庫找出 3-5 個最匹配的藥物
3. 回傳 JSON：
{{
    "has_medicine": true/false,
    "medicines": [
        {{
            "id": "藥物ID",
            "name": "中文名稱",
            "confidence": 0.95,
            "reason": "匹配理由"
        }}
    ]
}}
只回傳 JSON。"""

            # 調用 Gemini API
            logger.info(f"📤 使用 RAG 模式發送圖片到 Gemini API: {image_path}")

            api_url = (
                f"{self.base_url}/{self.model_name}:generateContent?key={self.api_key}"
            )

            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": image_b64,
                                }
                            },
                        ]
                    }
                ]
            }

            headers = {"Content-Type": "application/json"}
            response = requests.post(api_url, json=payload, headers=headers, timeout=60)

            logger.info(f"📥 Gemini API 回應狀態碼: {response.status_code}")

            if response.status_code != 200:
                error_detail = response.text
                logger.error(
                    f"✗ Gemini API 錯誤 ({response.status_code}): {error_detail}"
                )
                return self.recognize(image_path)  # 回退到普通模式

            # 解析回應
            response_data = response.json()

            if "candidates" not in response_data or not response_data["candidates"]:
                logger.warning("⚠️ Gemini 無候選回應")
                return []

            candidate = response_data["candidates"][0]
            if "content" not in candidate or "parts" not in candidate["content"]:
                logger.warning("⚠️ Gemini 回應無內容部分")
                return []

            result_text = ""
            for part in candidate["content"]["parts"]:
                if part.get("thought"):
                    continue
                if "text" in part:
                    result_text = part["text"]
            if not result_text:
                for part in candidate["content"]["parts"]:
                    if "text" in part:
                        result_text = part["text"]

            logger.info(f"✓ Gemini RAG 回應: {result_text[:100]}...")

            # 解析 JSON 結果
            medicines = self._parse_rag_response(result_text)
            logger.info(f"✓ RAG 識別完成，找到 {len(medicines)} 個結果")

            return medicines

        except Exception as e:
            logger.error(f"✗ RAG 識別失敗: {e}")
            import traceback

            logger.error(f"錯誤堆棧: {traceback.format_exc()}")
            # 回退到普通模式
            return self.recognize(image_path)

    def _parse_rag_response(self, response_text: str) -> List[Dict[str, Any]]:
        """解析 RAG 模式的 Gemini 回應"""
        medicines = []

        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            import re

            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                except json.JSONDecodeError:
                    logger.warning(f"⚠ 無法解析 RAG 回應: {response_text}")
                    return []
            else:
                logger.warning(f"⚠ 無法找到 JSON 在 RAG 回應中: {response_text}")
                return []

        if not data.get("has_medicine", False):
            return []

        # 提取藥物資訊
        for medicine in data.get("medicines", [])[:10]:
            medicines.append(
                {
                    "name": medicine.get("name", "未知藥物"),
                    "confidence": float(medicine.get("confidence", 0.5)),
                    "license_number": medicine.get("license_number", ""),
                    "drug_id": medicine.get("id", ""),
                    "reason": medicine.get("reason", ""),
                    "source": "gemini_rag",
                }
            )

        # 按信心度排序
        medicines.sort(key=lambda x: x["confidence"], reverse=True)

        return medicines[:10]

    def recognize_prescription(self, image_path: str) -> List[str]:
        """
        從藥單圖片中提取所有藥物名稱
        """
        try:
            image_file = Path(image_path)
            if not image_file.exists():
                raise FileNotFoundError(f"圖片檔案不存在: {image_path}")

            with open(image_file, "rb") as f:
                image_data = f.read()

            suffix = image_file.suffix.lower()
            mime_type_map = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }
            mime_type = mime_type_map.get(suffix, "image/jpeg")
            image_b64 = base64.standard_b64encode(image_data).decode("utf-8")

            prompt = """請分析這張醫院藥單/處方箋的照片。
請提取出上面每一項藥物的以下資訊，回傳 JSON 陣列：
- license_number: 許可證字號（如 A037598116、AC42626100 等，通常在藥名後面）
- chinese_name: 中文藥名（如 愛克痰、安鼻寧錠 等）
- english_name: 英文藥名（如 ACTEIN GRANULES、ANPIRIN TABLETS 等）
- route: 給藥途徑（如 口服、外用、注射 等）
- days: 天數（純數字，如 3、7、14）
- frequency: 服用頻率（如 三餐餐後、早晚餐後、睡前、需要時使用 等）
- dose_per_time: 每次劑量（如 1 TAB、1 pack、1 CC 等）
- total_quantity: 總量（如 共 9 TAB、共 6 TAB 等）
- ingredient: 成分名稱（如 ACETYLCYSTEINE、LORATADINE 等，通常在「成分名:」後面）

範例格式：
[
  {
    "license_number": "A037598116",
    "chinese_name": "愛克痰",
    "english_name": "ACTEIN GRANULES",
    "route": "口服",
    "days": 3,
    "frequency": "三餐餐後",
    "dose_per_time": "1 pack",
    "total_quantity": "共 9 Bot",
    "ingredient": "ACETYLCYSTEINE"
  }
]

規則：
1. 每一條藥物都要提取，不要遺漏
2. 如果某個欄位看不清楚，填空字串 ""，數字欄位填 0
3. 只回傳 JSON，不需要其他文字
4. 如果沒看到任何藥物，回傳 []"""

            api_url = (
                f"{self.base_url}/{self.model_name}:generateContent?key={self.api_key}"
            )
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": image_b64,
                                }
                            },
                        ]
                    }
                ]
            }
            headers = {"Content-Type": "application/json"}
            response = requests.post(api_url, json=payload, headers=headers, timeout=30)

            if response.status_code != 200:
                logger.error(f"✗ Gemini OCR API 錯誤: {response.text}")
                # 拋出 exception 讓 router 能往備用 key fallback
                raise Exception(
                    f"Gemini OCR HTTP {response.status_code}: {response.text[:200]}"
                )

            response_data = response.json()
            if "candidates" not in response_data or not response_data["candidates"]:
                logger.warning(f"⚠ 藥單 OCR: Gemini 無 candidates 回傳: {json.dumps(response_data, ensure_ascii=False)[:500]}")
                return []

            candidate = response_data["candidates"][0]
            if "content" not in candidate or "parts" not in candidate["content"]:
                logger.warning(f"⚠ 藥單 OCR: candidate 缺少 content/parts: {json.dumps(candidate, ensure_ascii=False)[:500]}")
                return []

            result_text = ""
            for part in candidate["content"]["parts"]:
                if part.get("thought"):
                    continue
                if "text" in part:
                    result_text = part["text"]

            if not result_text:
                # fallback: 取最後一個有 text 的 part (即使是 thought)
                for part in candidate["content"]["parts"]:
                    if "text" in part:
                        result_text = part["text"]

            logger.info(f"📄 藥單 OCR Gemini 回傳文字 (前300字): {result_text[:300]}")

            # 嘗試解析 JSON
            import re

            # 去除 markdown code fence
            clean_text = re.sub(r"```(?:json)?\s*", "", result_text)
            clean_text = clean_text.strip()

            json_match = re.search(r"\[.*\]", clean_text, re.DOTALL)
            if not json_match:
                logger.warning(f"⚠ 藥單 OCR: 回傳文字中找不到 JSON 陣列")
                return []

            parsed = json.loads(json_match.group())
            logger.info(f"📄 藥單 OCR: 解析到 {len(parsed)} 筆藥物資料")

            # 如果回傳的是新格式（dict 列表），轉換為向後相容的名稱列表
            # 同時保留結構化資料供後續比對使用
            if parsed and isinstance(parsed[0], dict):
                self._last_prescription_details = parsed
                logger.info(f"📄 藥單 OCR: 結構化資料已儲存 ({len(parsed)} 筆), keys: {list(parsed[0].keys())}")
                # 回傳中文名為主，英文名為輔的名稱列表
                names = []
                for item in parsed:
                    name = item.get("chinese_name", "") or item.get("english_name", "")
                    if name:
                        names.append(name)
                    else:
                        # 保留空位以對齊 index
                        names.append(f"未知藥物_{len(names)+1}")
                return names

            self._last_prescription_details = None
            logger.warning(f"⚠ 藥單 OCR: parsed 非 dict 列表, type={type(parsed[0]) if parsed else 'empty'}")
            return parsed

        except Exception as e:
            logger.error(f"✗ 藥單 OCR 失敗: {e}", exc_info=True)
            raise
