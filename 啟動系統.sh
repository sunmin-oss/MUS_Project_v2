#!/bin/bash

# macOS/Linux 啟動指令碼 - MUS2 藥物辨識系統

echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║     MUS2 藥物辨識系統 - 快速啟動                    ║"
echo "║   簡化版 / API 驅動 / 年長者友好設計              ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

# 檢查虛擬環境
if [ ! -d "venv" ]; then
    echo "⚠️  虛擬環境不存在，正在建立..."
    python3 -m venv venv
    echo "✓ 虛擬環境已建立"
    echo ""
fi

# 激活虛擬環境
source venv/bin/activate

# 檢查依賴
echo "📦 檢查依賴..."
pip show flask > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "⚠️  依賴未安裝，正在安裝..."
    pip install -r requirements.txt
    echo "✓ 依賴安裝完成"
else
    echo "✓ 依賴已安裝"
fi
echo ""

# 檢查 .env
if [ ! -f ".env" ]; then
    echo "⚠️  .env 檔案不存在！"
    echo ""
    echo "請按照以下步驟配置系統："
    echo ""
    echo "1. 複製 .env.example 為 .env"
    echo "   cp .env.example .env"
    echo ""
    echo "2. 編輯 .env 填入您的 API 密鑰"
    echo "   nano .env"
    echo ""
    echo "3. 儲存檔案後重新執行此啟動指令碼"
    echo ""
    exit 1
fi
echo "✓ .env 檔案已找到"
echo ""

# 檢查資料庫
if [ ! -f "drug_recognition.db" ]; then
    echo "⚠️  藥物資料庫不存在"
    echo "💡 提示：複製 ../MUS_Project/drug_recognition.db 以啟用搜尋功能"
    echo ""
fi

# 啟動應用
echo "🚀 正在啟動 MUS2 系統..."
echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║  系統已啟動！                                       ║"
echo "║  訪問: http://localhost:5000                        ║"
echo "║  按 Ctrl+C 停止伺服器                               ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

python main.py
