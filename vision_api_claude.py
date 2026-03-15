"""
==============================================
Claude Vision API 包裝器
==============================================

【功能說明】
使用 Anthropic Claude Vision API 進行藥物圖片識別。
此模組提供更智能的藥物識別，可理解上下文。

【API 文件】
https://www.anthropic.com/

【作者】MUS2 團隊
【日期】2025
"""

import requests
import base64
import logging
from typing import List, Dict, Any
import json

logger = logging.getLogger(__name__)


class ClaudeVisionRecognizer:
    """Claude Vision API 藥物識別器"""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        """
        初始化 Claude Vision 識別器

        參數:
            api_key: Anthropic Claude API 密鑰
            model: 使用的模型版本
        """
        if not api_key:
            raise ValueError("Claude API 密鑰未提供")

        self.api_key = api_key
        self.model = model
        self.endpoint = "https://api.anthropic.com/v1/messages"

        logger.info("✓ Claude Vision API 識別器已初始化")

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

            # 判斷圖片類型
            image_type = self._get_image_type(image_path)

            # 構建請求
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }

            payload = {
                "model": self.model,
                "max_tokens": 1024,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": f"image/{image_type}",
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": """請分析圖片中的藥物。回傳 JSON 格式的結果，包含以下資訊：
{
    "medicines": [
        {
            "name": "藥物名稱",
            "confidence": 0.95,
            "description": "簡短描述",
            "visual_features": "顏色、形狀等視覺特徵",
            "markings": "藥物上的刻印或標記"
        }
    ],
    "has_medicine": true,
    "notes": "其他備註"
}

如果圖片中沒有藥物或無法識別，請設定 has_medicine 為 false。
只回傳 JSON，不需額外文字。""",
                            },
                        ],
                    }
                ],
            }

            # 發送請求
            response = requests.post(
                self.endpoint, headers=headers, json=payload, timeout=30
            )
            response.raise_for_status()

            result = response.json()

            # 解析回應
            content = result.get("content", [{}])[0].get("text", "{}")

            # 嘗試解析 JSON
            try:
                data = json.loads(content)
                medicines = self._parse_medicines(data)
            except json.JSONDecodeError:
                logger.warning(f"⚠ 無法解析 Claude 回應: {content}")
                medicines = []

            logger.info(f"✓ 識別完成，找到 {len(medicines)} 個結果")
            return medicines

        except requests.exceptions.RequestException as e:
            logger.error(f"✗ API 請求失敗: {e}")
            raise Exception(f"Claude Vision API 錯誤: {str(e)}")
        except Exception as e:
            logger.error(f"✗ 識別過程出錯: {e}")
            raise Exception(f"識別失敗: {str(e)}")

    def _get_image_type(self, image_path: str) -> str:
        """取得圖片類型"""
        ext = image_path.lower().split(".")[-1]
        type_map = {
            "jpg": "jpeg",
            "jpeg": "jpeg",
            "png": "png",
            "gif": "gif",
            "webp": "webp",
        }
        return type_map.get(ext, "jpeg")

    def _parse_medicines(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析 Claude 回應中的藥物資訊"""
        medicines = []

        if not data.get("has_medicine", False):
            return medicines

        for medicine in data.get("medicines", [])[:10]:
            medicines.append(
                {
                    "name": medicine.get("name", ""),
                    "confidence": medicine.get("confidence", 0.5),
                    "description": medicine.get("description", ""),
                    "visual_features": medicine.get("visual_features", ""),
                    "markings": medicine.get("markings", ""),
                    "source": "claude_vision",
                }
            )

        # 按信心度排序
        medicines.sort(key=lambda x: x["confidence"], reverse=True)

        return medicines[:10]  # 最多回傳 10 個結果
