FROM python:3.10-slim

# 設置工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴檔案
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用檔案
COPY . .

# 建立上傳目錄
RUN mkdir -p uploads

# 暴露端口
EXPOSE 5000

# 設置環境變數
ENV FLASK_ENV=production
ENV FLASK_DEBUG=False

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/health')"

# 啟動應用
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--timeout", "120", "main:app"]
