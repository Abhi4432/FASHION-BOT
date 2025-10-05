import sqlite3
import os
import pandas as pd
from db.config import DB_PATH

#DB_PATH = os.path.abspath("backend/fashion_ai.db")
CLEAN_DATA_PATH = os.path.abspath("data/fashion_dataset_clean.csv")


def seed_products():
    if not os.path.exists(CLEAN_DATA_PATH):
        raise FileNotFoundError(f"CSV not found at {CLEAN_DATA_PATH}")

    df = pd.read_csv(CLEAN_DATA_PATH)
    inserted = 0
    skipped = 0

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for i, row in df.iterrows():
        p_id = str(row.get("p_id", "")).strip()
        name = str(row.get("name", "")).strip()
        price = row.get("price", None)
        if not p_id or not name or price is None:
            skipped += 1
            continue

        try:
            # Inside cursor.execute(...)
            cursor.execute("""
                INSERT OR REPLACE INTO PRODUCTS (
                    P_ID, NAME, PRICE, COLOUR, BRAND, IMG,
                    RATINGCOUNT, AVG_RATING, DESCRIPTION, P_ATTRIBUTES,
                    TOP_TYPE, SLEEVE_LENGTH, OCCASION, PRINT_PATTERN, FABRIC,
                    HAS_DUPATTA, IS_SUSTAINABLE, SEARCH_TEXT
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p_id, name, float(price), str(row.get("colour", "")), str(row.get("brand", "")),
                str(row.get("img", "")), int(row.get("ratingCount", 0)), float(row.get("avg_rating", 0.0)),
                str(row.get("description", "")), str(row.get("p_attributes", "")),
                str(row.get("top_type", "")), str(row.get("sleeve_length", "")),
                str(row.get("occasion", "")), str(row.get("pattern", "")), str(row.get("fabric", "")),
                int(row.get("has_dupatta", 0)), int(row.get("is_sustainable", 0)), str(row.get("search_text", ""))
            ))

            inserted += 1
        except Exception as e:
            skipped += 1
            print(f"Failed to insert row {i}: {e}")

    conn.commit()
    conn.close()
    print(f"Products seeded: {inserted}, skipped: {skipped}")


if __name__ == "__main__":
    seed_products()

