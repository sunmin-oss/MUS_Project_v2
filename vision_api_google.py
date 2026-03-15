"""
==============================================
Google Cloud Vision API 包裝器
==============================================

【功能說明】
使用 Google Cloud Vision API 進行藥物圖片識別。

【API 文件】
https://cloud.google.com/vision/docs/detecting-labels

【作者】MUS2 團隊
【日期】2025
"""

import requests
import base64
import logging
from typing import List, Dict, Any
import json

logger = logging.getLogger(__name__)


class GoogleVisionRecognizer:
    """Google Vision API 藥物識別器"""

    def __init__(self, api_key: str):
        """
        初始化 Google Vision 識別器

        參數:
            api_key: Google Cloud Vision API 密鑰
        """
        if not api_key:
            raise ValueError("Google Vision API 密鑰未提供")

        self.api_key = api_key
        self.endpoint = "https://vision.googleapis.com/v1/images:annotate"

        logger.info("✓ Google Vision API 識別器已初始化")

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
            # 讀取圖片並編碼
            with open(image_path, "rb") as f:
                image_data = base64.standard_b64encode(f.read()).decode("utf-8")

            # 構建請求
            request_body = {
                "requests": [
                    {
                        "image": {"content": image_data},
                        "features": [
                            {"type": "LABEL_DETECTION", "maxResults": 10},
                            {"type": "TEXT_DETECTION", "maxResults": 5},
                            {"type": "OBJECT_LOCALIZATION", "maxResults": 10},
                        ],
                    }
                ]
            }

            # 發送請求
            response = requests.post(
                f"{self.endpoint}?key={self.api_key}", json=request_body, timeout=30
            )
            response.raise_for_status()

            result = response.json()

            # 解析回應
            annotations = result.get("responses", [{}])[0]

            # 提取藥物相關的標籤
            medicines = self._extract_medicines(
                annotations.get("labelAnnotations", []),
                annotations.get("textAnnotations", []),
                annotations.get("localizedObjectAnnotations", []),
            )

            logger.info(f"✓ 識別完成，找到 {len(medicines)} 個結果")
            return medicines

        except requests.exceptions.RequestException as e:
            logger.error(f"✗ API 請求失敗: {e}")
            raise Exception(f"Google Vision API 錯誤: {str(e)}")
        except Exception as e:
            logger.error(f"✗ 識別過程出錯: {e}")
            raise Exception(f"識別失敗: {str(e)}")

    def _extract_medicines(
        self, labels: List[Dict], texts: List[Dict], objects: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        從 API 回應中提取藥物資訊
        """
        medicines = []

        # 藥物相關的關鍵詞
        medicine_keywords = [
            "medicine",
            "pill",
            "tablet",
            "capsule",
            "drug",
            "medication",
            "藥",
            "藥片",
            "藥丸",
            "膠囊",
            "藥物",
            "用藥",
        ]

        # 從標籤中提取
        for label in labels[:10]:
            description = label.get("description", "").lower()
            confidence = label.get("score", 0)

            # 檢查是否為藥物相關
            if (
                any(keyword in description for keyword in medicine_keywords)
                or confidence > 0.5
            ):
                medicines.append(
                    {
                        "name": label.get("description", ""),
                        "confidence": confidence,
                        "source": "label_detection",
                    }
                )

        # 從文字識別中提取（藥物通常有刻印標記）
        ocr_texts = []
        if texts and len(texts) > 0:
            # 第一個是整體文字，跳過
            ocr_texts = [
                t.get("description", "").strip()
                for t in texts[1:]
                if t.get("description")
            ]

        if ocr_texts:
            ocr_result = " ".join(ocr_texts)
            if ocr_result.strip():
                medicines.append(
                    {
                        "name": ocr_result[:100],  # 限制長度
                        "confidence": 0.6,  # OCR 結果置信度較低
                        "source": "text_detection",
                        "description": "從藥物刻印識別",
                    }
                )

        # 從物體偵測中提取
        for obj in objects[:5]:
            name = obj.get("name", "")
            confidence = obj.get("score", 0)

            if any(keyword in name.lower() for keyword in medicine_keywords):
                medicines.append(
                    {
                        "name": name,
                        "confidence": confidence,
                        "source": "object_localization",
                    }
                )

        # 去重並按信心度排序
        seen = set()
        unique_medicines = []
        for medicine in medicines:
            name_lower = medicine["name"].lower()
            if name_lower not in seen:
                seen.add(name_lower)
                unique_medicines.append(medicine)

        # 按信心度排序
        unique_medicines.sort(key=lambda x: x["confidence"], reverse=True)

        return unique_medicines[:10]  # 最多回傳 10 個結果
