#!/bin/sh
# Docker entrypoint: 確保資料目錄與 DB 檔案存在
set -e

mkdir -p /app/data /app/uploads

# 若 data/ 下無 DB 檔案且專案根有預設 DB，則複製過去
if [ ! -f /app/data/drug_recognition.db ] && [ -f /app/drug_recognition.db ]; then
    cp /app/drug_recognition.db /app/data/drug_recognition.db
    echo "✓ 已複製預設資料庫到 /app/data/"
fi

exec "$@"
