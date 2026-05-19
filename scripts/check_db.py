import sqlite3
from pathlib import Path

db_path = "drug_recognition.db"
if Path(db_path).exists():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 列出所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("📊 資料庫表格：", [t[0] for t in tables])

    for table_name in [t[0] for t in tables]:
        print(f'\n📋 表格 "{table_name}" 的欄位：')

        # 檢查表結構
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        for i, col in enumerate(columns[:8]):
            print(f"  {i+1}. {col[1]}")
        if len(columns) > 8:
            print(f"  ... 共 {len(columns)} 欄位")

        # 檢查行數
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"💊 行數: {count} 個")

    conn.close()
else:
    print("❌ 資料庫不存在")
