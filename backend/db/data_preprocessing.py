import pandas as pd
import os
from bs4 import BeautifulSoup
import ast

RAW_DATA_PATH = os.path.abspath("data/fashion_dataset.csv")
CLEAN_DATA_PATH = os.path.abspath("data/fashion_dataset_clean.csv")

def clean_html(text):
    if pd.isna(text):
        return ""
    return BeautifulSoup(text, "html.parser").get_text(separator=" ", strip=True)

def safe_str(x):
    return str(x).strip().lower() if not pd.isna(x) else "unknown"

def preprocess_data():
    if not os.path.exists(RAW_DATA_PATH):
        raise FileNotFoundError(f"❌ CSV not found at {RAW_DATA_PATH}")

    df = pd.read_csv(RAW_DATA_PATH)

    # ----------------------------
    # 1️⃣ Handle p_id as string
    df = df[pd.notna(df["p_id"])]
    df["p_id"] = df["p_id"].astype(str)

    # 2️⃣ Fill missing numeric columns
    df["price"] = df["price"].fillna(0.0)
    df["ratingCount"] = df["ratingCount"].fillna(0).astype(int)
    df["avg_rating"] = df["avg_rating"].fillna(0.0)

    # 3️⃣ Fill missing text columns
    text_cols = ["name", "colour", "brand", "img", "description"]
    for col in text_cols:
        df[col] = df[col].fillna("Unknown").astype(str).str.strip()

    # 4️⃣ Clean HTML from description
    df["description"] = df["description"].apply(clean_html)

    # 5️⃣ Parse attributes
    def parse_attributes(attr_str):
        try:
            return ast.literal_eval(attr_str)
        except Exception:
            return {}

    df["p_attributes"] = df["p_attributes"].apply(parse_attributes)

    # 6️⃣ Feature engineering
    df["top_type"] = df["p_attributes"].apply(lambda x: safe_str(x.get("Top Type", x.get("Top", "unknown"))))
    df["sleeve_length"] = df["p_attributes"].apply(lambda x: safe_str(x.get("Sleeve Length", "unknown")))
    df["occasion"] = df["p_attributes"].apply(lambda x: safe_str(x.get("Occasion", "casual")))
    df["pattern"] = df["p_attributes"].apply(lambda x: safe_str(x.get("Print or Pattern Type", "unknown")))
    df["fabric"] = df["p_attributes"].apply(lambda x: safe_str(x.get("Top Fabric", "unknown")))
    df["has_dupatta"] = df["p_attributes"].apply(lambda x: 1 if x.get("Dupatta", "NA").lower() == "with dupatta" else 0)
    df["is_sustainable"] = df["p_attributes"].apply(lambda x: 1 if "sustainable" in safe_str(x.get("Sustainable", "")) else 0)

    # 7️⃣ Create search text for retrieval/embedding
    df["search_text"] = (
        df["name"].str.lower() + " " +
        df["brand"].str.lower() + " " +
        df["colour"].str.lower() + " " +
        df["pattern"].str.lower() + " " +
        df["occasion"].str.lower() + " " +
        df["fabric"].str.lower()
    )

    # 8️⃣ Drop duplicates on p_id
    df = df.drop_duplicates(subset=["p_id"], keep="first")

    # 9️⃣ Save clean CSV
    df.to_csv(CLEAN_DATA_PATH, index=False)
    print(f"✅ Cleaned dataset saved to {CLEAN_DATA_PATH}")
    print(f"📊 Total records after cleaning: {len(df)}")

if __name__ == "__main__":
    preprocess_data()


