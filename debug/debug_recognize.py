"""
診斷 recognize API 的問題
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from config import config
from vision_api_gemini import GeminiVisionRecognizer
from PIL import Image, ImageDraw
import io
import tempfile

# 初始化認識器
print("🔧 初始化 Gemini Vision API...")
try:
    recognizer = GeminiVisionRecognizer(config.GEMINI_API_KEY)
    print("✓ 識別器已初始化")
except Exception as e:
    print(f"✗ 初始化失敗: {e}")
    sys.exit(1)

# 創建測試圖片
print("\n🎨 建立測試圖片...")
try:
    img = Image.new("RGB", (200, 200), color="white")
    draw = ImageDraw.Draw(img)

    # 畫紅色圓形（模擬藥片）
    draw.ellipse([50, 50, 150, 150], fill="red", outline="darkred")
    draw.text((60, 85), "TEST", fill="white")

    # 保存為臨時檔案
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img.save(f, format="PNG")
        temp_path = f.name

    print(f"✓ 測試圖片已建立: {temp_path}")
except Exception as e:
    print(f"✗ 圖片建立失敗: {e}")
    sys.exit(1)

# 嘗試識別
print("\n🔍 嘗試識別圖片...")
try:
    results = recognizer.recognize(temp_path)
    print(f"✓ 識別成功！")
    print(f"結果數量: {len(results)}")
    for i, item in enumerate(results):
        print(f"\n  結果 {i+1}:")
        for key, value in item.items():
            print(f"    {key}: {value}")
except Exception as e:
    print(f"✗ 識別失敗")
    print(f"錯誤信息: {e}")
    import traceback

    traceback.print_exc()
finally:
    # 清理臨時檔案
    if os.path.exists(temp_path):
        os.remove(temp_path)
