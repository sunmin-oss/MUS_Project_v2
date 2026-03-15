"""
==============================================
辛苦的 MUS2 專題 - 測試工具集
==============================================

此模組提供用於本地測試的實用函式。

【使用方式】
python test_utils.py

【功能】
- 測試 API 端點
- 驗證 Vision API 連線
- 檢查資料庫狀態
"""

import requests
import json
import sys
from pathlib import Path

# 配置
API_BASE_URL = "http://localhost:5000"
API_ENDPOINTS = {
    "health": "/api/health",
    "search": "/api/search",
}


def print_header(title):
    """打印標題"""
    print("\n" + "=" * 50)
    print(f"  {title}")
    print("=" * 50)


def test_api_health():
    """測試 API 健康狀態"""
    print_header("🏥 API 健康檢查")

    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✓ API 健康")
            print(f"  狀態: {data.get('status')}")
            print(f"  Vision API: {data.get('services', {}).get('vision_api')}")
            print(f"  資料庫: {data.get('services', {}).get('database')}")
            return True
        else:
            print(f"✗ API 異常 (HTTP {response.status_code})")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ 無法連接到 API")
        print(f"  請檢查伺服器是否在 {API_BASE_URL} 運行")
        return False
    except Exception as e:
        print(f"✗ 測試失敗: {e}")
        return False


def test_database():
    """測試資料庫"""
    print_header("💾 資料庫檢查")

    db_path = Path("drug_recognition.db")
    if db_path.exists():
        print(f"✓ 資料庫存在")
        print(f"  大小: {db_path.stat().st_size / (1024*1024):.1f} MB")

        # 嘗試查詢
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/search",
                json={"query": "test", "limit": 1},
                timeout=5,
            )
            if response.status_code == 200:
                print(f"✓ 資料庫可查詢")
            else:
                print(f"⚠ 資料庫可能有問題 (HTTP {response.status_code})")
        except Exception as e:
            print(f"⚠ 無法測試資料庫查詢: {e}")
    else:
        print("⚠ 資料庫不存在")
        print("  💡 提示: 複製 ../MUS_Project/drug_recognition.db")
        return False

    return True


def test_config():
    """測試配置"""
    print_header("⚙️ 配置檢查")

    env_path = Path(".env")
    if env_path.exists():
        print("✓ .env 檔案存在")

        # 讀取並檢查重要配置
        with open(env_path, "r", encoding="utf-8") as f:
            content = f.read()
            if "API_PROVIDER" in content:
                print("  ✓ 配置了 API_PROVIDER")
            if "GOOGLE_VISION_API_KEY" in content or "CLAUDE_API_KEY" in content:
                print("  ✓ 配置了 API 密鑰")
    else:
        print("✗ .env 檔案不存在")
        print("  請複製 .env.example 為 .env 並填入 API 密鑰")
        return False

    return True


def test_search(query="普拿疼"):
    """測試搜尋功能"""
    print_header("🔍 搜尋功能測試")

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/search", json={"query": query, "limit": 3}, timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                results = data.get("results", [])
                print(f"✓ 搜尋成功 (找到 {len(results)} 個結果)")
                for i, result in enumerate(results[:3], 1):
                    print(f"  {i}. {result.get('chinese_name', 'Unknown')}")
                return True
            else:
                print(f"⚠ 搜尋返回空結果")
                return False
        else:
            print(f"✗ 搜尋失敗 (HTTP {response.status_code})")
            return False
    except Exception as e:
        print(f"✗ 搜尋測試失敗: {e}")
        return False


def check_python_packages():
    """檢查 Python 依賴"""
    print_header("📦 Python 依賴檢查")

    required_packages = ["flask", "requests", "flask_cors"]
    missing = []

    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package}")
            missing.append(package)

    if missing:
        print(f"\n⚠ 缺少依賴: {', '.join(missing)}")
        print(f"  請執行: pip install -r requirements.txt")
        return False

    return True


def main():
    """運行所有測試"""
    print("\n" + "╔" + "=" * 48 + "╗")
    print("║" + " " * 10 + "MUS2 系統診斷工具" + " " * 22 + "║")
    print("╚" + "=" * 48 + "╝")

    results = {
        "Python 依賴": check_python_packages(),
        "配置檢查": test_config(),
        "資料庫檢查": test_database(),
        "API 健康檢查": test_api_health(),
    }

    # 可選：搜尋功能測試
    # results["搜尋功能"] = test_search()

    # 總結
    print_header("📊 測試總結")
    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")

    print(f"\n結果: {passed}/{total} 個測試通過")

    if passed == total:
        print("\n✅ 所有系統已就緒！")
        print("🚀 執行 'python main.py' 啟動系統")
    else:
        print("\n⚠️ 部分系統需要配置，請參考上述警告信息")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
