import sqlite3
import os
import random
from datetime import datetime, timedelta
import pandas as pd
from db.config import DB_PATH
# DB_PATH = os.path.abspath("backend/db/fashion_ai.db")
CLEAN_DATA_PATH = os.path.abspath("data/fashion_dataset_clean.csv")
STATUSES = ["ordered", "packed", "shipped", "out for delivery", "delivered"]
EXPORT_PATH = os.path.join("data", "orders.csv")

def generate_mobile_string():
    return str(random.randint(1000000000, 9999999999))

def seed_orders(num_orders=50):
    df_products = pd.read_csv(CLEAN_DATA_PATH)
    product_ids = df_products["p_id"].dropna().astype(str).tolist()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all users
    cursor.execute("SELECT USER_ID FROM USERS")
    users = [row[0] for row in cursor.fetchall()]
    if not users:
        raise RuntimeError("No users found. Seed users first.")

    # Check existing orders
    cursor.execute("SELECT COUNT(*) FROM ORDERS")
    existing_count = cursor.fetchone()[0]

    # Delete excess orders if num_orders < existing
    if existing_count > num_orders:
        delete_count = existing_count - num_orders
        cursor.execute(f"DELETE FROM ORDERS WHERE ORDER_ID IN (SELECT ORDER_ID FROM ORDERS ORDER BY ORDER_ID DESC LIMIT {delete_count})")
        print(f"Deleted {delete_count} excess orders")
        existing_count = num_orders

    to_insert = max(0, num_orders - existing_count)
    inserted = 0

    for _ in range(to_insert):
        try:
            product_id = random.choice(product_ids)
            user_id = random.choice(users)
            order_date = datetime.now() - timedelta(days=random.randint(1, 30))
            shipping_date = order_date + timedelta(days=random.randint(1, 3))
            delivery_date = shipping_date + timedelta(days=random.randint(2, 7))
            status = random.choice(STATUSES)
            amount = random.randint(500, 5000)
            delivery_partner_no = generate_mobile_string()

            # Get the product description from the DataFrame
            product_row = df_products[df_products["p_id"].astype(str) == str(product_id)]
            product_description = product_row["description"].values[0] if not product_row.empty else ""

            cursor.execute("""
                INSERT INTO ORDERS (
                    PRODUCT_ID, USER_ID, PRODUCT_DESCRIPTION,
                    ORDER_DATE, SHIPPING_DATE, DELIVERY_DATE,
                    AMOUNT, STATUS, DELIVERY_PARTNER_NO
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (product_id, user_id, product_description,
                  order_date.date(), shipping_date.date(), delivery_date.date(),
                  amount, status, delivery_partner_no))
            inserted += 1
        except Exception as e:
            print(f"Failed to insert order: {e}")

    conn.commit()

    # Export to CSV
    df_orders = pd.read_sql_query("SELECT * FROM ORDERS", conn)
    df_orders.to_csv(EXPORT_PATH, index=False)
    print(f"✅ Orders seeded: {inserted}, total now: {len(df_orders)}")
    print(f"✅ ORDERS table exported to {EXPORT_PATH}")

    conn.close()

if __name__ == "__main__":
    seed_orders(num_orders=200)





