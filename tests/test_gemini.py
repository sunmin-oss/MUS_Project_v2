"""
==============================================
Gemini API 快速測試工具
==============================================

此工具專門用於測試 Gemini Vision API 的連接和功能。

【使用方式】
python test_gemini.py

【功能】
1. 檢查 Gemini API 金鑰配置
2. 驗證 API 連接
3. 測試圖片識別功能
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()


def print_header(title):
    """打印標題"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def check_dependencies():
    """檢查依賴安裝"""
    print_header("📦 檢查依賴")

    required_packages = {
        "google.generativeai": "google-generativeai",
        "flask": "Flask",
        "requests": "requests",
        "dotenv": "python-dotenv",
    }

    missing = []
    for package, pip_name in required_packages.items():
        try:
            __import__(package)
            print(f"  ✓ {pip_name}")
        except ImportError:
            print(f"  ✗ {pip_name} (未安裝)")
            missing.append(pip_name)

    if missing:
        print(f"\n⚠️ 缺少依賴: {', '.join(missing)}")
        print(f"請執行: pip install -r requirements.txt")
        return False

    return True


def check_api_key():
    """檢查 API 金鑰配置"""
    print_header("🔑 API 金鑰檢查")

    api_key = os.getenv("GEMINI_API_KEY")
    api_provider = os.getenv("API_PROVIDER", "gemini")

    print(f"  API_PROVIDER: {api_provider}")

    if not api_key:
        print("  ✗ GEMINI_API_KEY 未設置")
        print("\n  請在 .env 檔案中設置:")
        print("  GEMINI_API_KEY=your_api_key_here")
        return False

    if api_key.startswith("your_"):
        print("  ✗ GEMINI_API_KEY 未填寫實際值")
        print(f"  目前值: {api_key}")
        return False

    # 顯示金鑰的一部分（隱藏敏感資訊）
    masked_key = api_key[:10] + "*" * (len(api_key) - 15) + api_key[-5:]
    print(f"  ✓ GEMINI_API_KEY 已設置: {masked_key}")
    return True


def test_api_connection():
    """測試 API 連接"""
    print_header("🌐 API 連接測試")

    try:
        import google.generativeai as genai

        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)

        # 嘗試列出模型
        print("  正在連接 Gemini API...")
        models = genai.list_models()
        model_list = [m.name for m in models if "vision" in m.name.lower()]

        if model_list:
            print(f"  ✓ API 連接成功")
            print(f"  可用的 Vision 模型: {model_list}")
            return True
        else:
            print("  ✓ API 連接成功 (但未找到 Vision 模型)")
            return True

    except Exception as e:
        print(f"  ✗ API 連接失敗")
        print(f"  錯誤: {str(e)}")
        return False


def test_vision_recognition():
    """測試圖片識別功能"""
    print_header("🖼️ Vision 識別測試")

    try:
        from vision_api_gemini import GeminiVisionRecognizer

        api_key = os.getenv("GEMINI_API_KEY")
        recognizer = GeminiVisionRecognizer(api_key)

        # 建立測試圖片 (簡單的純色圖片)
        test_image_path = create_test_image()

        if not test_image_path:
            print("  ✗ 無法建立測試圖片")
            return False

        print(f"  正在識別圖片: {test_image_path}")
        results = recognizer.recognize(test_image_path)

        if results:
            print(f"  ✓ 識別成功，找到 {len(results)} 個結果")
            for i, item in enumerate(results[:3], 1):
                print(
                    f"    {i}. {item.get('name', 'Unknown')} (信心度: {item.get('confidence', 0):.2%})"
                )
            return True
        else:
            print(f"  ⚠️ 未識別出任何結果（但 API 執行正常）")
            return True

    except Exception as e:
        print(f"  ✗ 識別測試失敗")
        print(f"  錯誤: {str(e)}")
        return False

    finally:
        # 清理測試圖片
        if Path(test_image_path).exists():
            Path(test_image_path).unlink()


def create_test_image():
    """建立測試圖片（簡單的 PNG）"""
    try:
        from PIL import Image

        # 建立一個簡單的白色圖片
        img = Image.new("RGB", (100, 100), color="white")

        # 在圖片上寫入測試文字
        from PIL import ImageDraw

        draw = ImageDraw.Draw(img)
        draw.text((10, 45), "TEST", fill="black")

        test_image_path = "test_image_temp.png"
        img.save(test_image_path)

        return test_image_path

    except ImportError:
        print("    提示: 安裝 Pillow 以支援圖片生成")
        print("    pip install Pillow")
        return None
    except Exception as e:
        print(f"    建立測試圖片失敗: {e}")
        return None


def main():
    """運行所有測試"""
    print("\n" + "╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "Gemini Vision API 測試工具" + " " * 15 + "║")
    print("╚" + "=" * 58 + "╝")

    # 運行測試
    tests = {
        "依賴檢查": check_dependencies,
        "API 金鑰": check_api_key,
        "API 連接": test_api_connection,
        # "Vision 識別": test_vision_recognition,  # 可選，需要真實圖片
    }

    results = {}
    for test_name, test_func in tests.items():
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"  ✗ 測試異常: {e}")
            results[test_name] = False

    # 總結
    print_header("📊 測試結果總結")
    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")

    print(f"\n結果: {passed}/{total} 個測試通過")

    if passed == total:
        print("\n✅ Gemini API 配置完成，可以啟動系統！")
        print("   執行: python main.py")
    else:
        print("\n⚠️ 部分測試未通過，請檢查上述信息")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
