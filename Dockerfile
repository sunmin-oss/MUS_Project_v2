FROM python:3.13-slim

# 設置工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc curl \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴檔案
COPY requirements.txt .

# 安裝 Python 依賴（含 gunicorn）
RUN pip install --no-cache-dir -r requirements.txt gunicorn>=22.0

# 複製應用檔案
COPY . .

# 建立必要目錄
RUN mkdir -p uploads medicine_photos data

# 設定 entrypoint
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# 暴露端口
EXPOSE 5000

# 設置環境變數
ENV FLASK_ENV=production
ENV FLASK_DEBUG=False
ENV PYTHONUNBUFFERED=1

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# 啟動應用（單 worker 避免 SQLite 鎖）
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["gunicorn", "-w", "1", "--threads", "4", "-b", "0.0.0.0:5000", "--timeout", "120", "--access-logfile", "-", "main:app"]
