import sqlite3
from typing import Dict, Any, Optional
from db.config import DB_PATH

def sql_node(relevant_data: Dict[str, Any], user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Smart SQL retriever for both orders and products.
    Detects whether to fetch by order_id or product fields.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        order_id = relevant_data.get("order_id")
        product_id = relevant_data.get("product_id")

        # 🧠 1️⃣ ORDER LOOKUP (if order_id exists)
        if order_id:
            cursor.execute("""
                SELECT 
                    o.ORDER_ID, o.PRODUCT_ID, o.USER_ID, o.STATUS, o.ORDER_DATE,
                    o.SHIPPING_DATE, o.DELIVERY_DATE, o.AMOUNT,
                    p.NAME, p.PRICE, p.BRAND, p.COLOUR, p.IMG, p.DESCRIPTION
                FROM ORDERS o
                JOIN PRODUCTS p ON o.PRODUCT_ID = p.P_ID
                WHERE o.ORDER_ID = ? AND o.USER_ID = ?
            """, (order_id, user_id))
            row = cursor.fetchone()

            if not row:
                return {"error": f"No order found for order_id {order_id} and user {user_id}"}

            keys = [
                "order_id", "product_id", "user_id", "status", "order_date",
                "shipping_date", "delivery_date", "amount",
                "name", "price", "brand", "colour", "img", "description"
            ]
            return {"type": "order", **dict(zip(keys, row))}

        # 🧠 2️⃣ PRODUCT LOOKUP (fallback or explicit)
        # Build dynamic search filters
        filters, params = [], []
        search_fields = [
            "product_id", "name", "brand", "colour", "fabric",
            "occasion", "print_pattern", "top_type", "sleeve_length", "description"
        ]

        for field in search_fields:
            if val := relevant_data.get(field):
                filters.append(f"{field.upper()} LIKE ?")
                params.append(f"%{val}%")

        if not filters:
            return {"error": "No valid product filters provided."}

        where_clause = " OR ".join(filters)
        query = f"""
            SELECT P_ID, NAME, PRICE, COLOUR, BRAND, IMG, DESCRIPTION
            FROM PRODUCTS
            WHERE {where_clause}
            ORDER BY RANDOM() LIMIT 1
        """

        cursor.execute(query, params)
        row = cursor.fetchone()
        if not row:
            return {"error": "No matching product found."}

        keys = ["product_id", "name", "price", "colour", "brand", "img", "description"]
        return {"type": "product", **dict(zip(keys, row))}

    except sqlite3.Error as e:
        return {"error": f"Database error: {e}"}

    finally:
        conn.close()


