@echo off
REM Windows 批次檔 - 啟動 MUS2 藥物辨識系統
REM 使用方式: 雙擊此檔案即可啟動

setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════╗
echo ║     MUS2 藥物辨識系統 - 快速啟動                    ║
echo ║   簡化版 / API 驅動 / 年長者友好設計              ║
echo ╚════════════════════════════════════════════════════╝
echo.

REM 檢查虛擬環境是否存在
if not exist "venv\" (
    echo ⚠️  虛擬環境不存在，正在建立...
    python -m venv venv
    echo ✓ 虛擬環境已建立
    echo.
)

REM 激活虛擬環境
call venv\Scripts\activate.bat

REM 檢查依賴是否安裝
echo 📦 檢查依賴...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo ⚠️  依賴未安裝，正在安裝...
    pip install -r requirements.txt
    echo ✓ 依賴安裝完成
) else (
    echo ✓ 依賴已安裝
)
echo.

REM 檢查 .env 檔案
if not exist ".env" (
    echo ⚠️  .env 檔案不存在！
    echo.
    echo 請按照以下步驟配置系統：
    echo.
    echo 1. 複製 .env.example 為 .env
    echo    copy .env.example .env
    echo.
    echo 2. 編輯 .env 填入您的 API 密鑰
    echo    - Google Vision API: GOOGLE_VISION_API_KEY
    echo    - Claude API: CLAUDE_API_KEY
    echo.
    echo 3. 儲存檔案後重新執行此啟動指令碼
    echo.
    pause
    exit /b 1
)
echo ✓ .env 檔案已找到
echo.

REM 檢查資料庫（可選）
if not exist "drug_recognition.db" (
    echo ⚠️  藥物資料庫不存在
    echo 💡 提示：複製 ../MUS_Project/drug_recognition.db 以啟用搜尋功能
    echo.
) else (
    echo ✓ 藥物資料庫已找到
)
echo.

REM 啟動應用
echo 🚀 正在啟動 MUS2 系統...
echo.
echo ╔════════════════════════════════════════════════════╗
echo ║  系統已啟動！                                       ║
echo ║  訪問: http://localhost:5000                        ║
echo ║  按 Ctrl+C 停止伺服器                               ║
echo ╚════════════════════════════════════════════════════╝
echo.

python main.py

pause
