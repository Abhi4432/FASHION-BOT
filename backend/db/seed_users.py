import sqlite3
import os
import hashlib
from faker import Faker
import pandas as pd
from db.config import DB_PATH

#DB_PATH = os.path.abspath("data/fashion_ai.db")
NUM_USERS = 50
EXPORT_PATH = os.path.join("data", "users.csv")
fake = Faker()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def seed_users(num_users=NUM_USERS):
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check current user count
    cursor.execute("SELECT COUNT(*) FROM USERS")
    existing_count = cursor.fetchone()[0]

    # Delete excess users if num_users < existing
    if existing_count > num_users:
        delete_count = existing_count - num_users
        cursor.execute(f"DELETE FROM USERS WHERE USER_ID IN (SELECT USER_ID FROM USERS ORDER BY USER_ID DESC LIMIT {delete_count})")
        print(f"Deleted {delete_count} excess users")
        existing_count = num_users

    # Insert new users if needed
    to_insert = max(0, num_users - existing_count)
    inserted = 0
    for _ in range(to_insert):
        try:
            username = fake.user_name()
            email = fake.email()
            password = hash_password("password123")
            cursor.execute("INSERT INTO USERS (USERNAME, EMAIL, PASSWORD) VALUES (?, ?, ?)",
                           (username, email, password))
            inserted += 1
        except sqlite3.IntegrityError:
            continue

    conn.commit()

    # Export to CSV
    df = pd.read_sql_query("SELECT * FROM USERS", conn)
    df.to_csv(EXPORT_PATH, index=False)
    print(f"✅ Users seeded: {inserted}, total now: {len(df)}")
    print(f"✅ USERS table exported to {EXPORT_PATH}")

    conn.close()

if __name__ == "__main__":
    seed_users(num_users=80)


