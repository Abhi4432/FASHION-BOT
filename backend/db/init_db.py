import sqlite3
import os
from db.config import DB_PATH
#DB_PATH = os.path.abspath("backend/db/fashion_ai.db")
SCHEMA_PATH = os.path.abspath("db/schema.sql")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        cursor.executescript(f.read())
    conn.commit()
    conn.close()
    print(f"✅ Database initialized at {DB_PATH}")

if __name__ == "__main__":
    init_db()
