import sqlite3
import os
from typing import Dict, Any, Optional
from db.config import DB_PATH

def sql_node(field_name: str, field_value: str, user_id: Optional[int] = None) -> Dict[str, Any]:
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT ORDER_ID, USER_ID FROM ORDERS WHERE USER_ID = 1")
        print("DEBUG: All orders for user 1:", cursor.fetchall())

        if field_name == "order_id":
            print("DEBUG: Querying order_id:", repr(field_value), "user_id:", repr(user_id))
            try:
                order_id_int = int(float(field_value))
                user_id_int = int(user_id)
            except Exception as e:
                return {"error": f"Invalid order_id or user_id: {e}"}
            cursor.execute("""
                SELECT 
                    o.ORDER_ID, o.PRODUCT_ID, o.USER_ID, o.PRODUCT_DESCRIPTION, o.ORDER_DATE, o.SHIPPING_DATE, o.DELIVERY_DATE, o.AMOUNT, o.STATUS, o.DELIVERY_PARTNER_NO,
                    p.NAME, p.PRICE, p.COLOUR, p.BRAND, p.IMG, p.RATINGCOUNT, p.AVG_RATING, p.DESCRIPTION
                FROM ORDERS o
                JOIN PRODUCTS p ON o.PRODUCT_ID = p.P_ID
                WHERE o.ORDER_ID = ? AND o.USER_ID = ?
            """, (order_id_int, user_id_int))
            row = cursor.fetchone()
            if row:
                keys = [
                    "order_id", "product_id", "user_id", "product_description", "order_date", "shipping_date", "delivery_date", "amount", "status", "delivery_partner_no",
                    "product_name", "product_price", "product_colour", "product_brand", "product_img", "product_ratingcount", "product_avg_rating", "product_description"
                ]
                return dict(zip(keys, row))
            else:
                return {"error": "Order not found or does not belong to this user."}

        elif field_name == "product_id":
            cursor.execute("""
                SELECT P_ID, NAME, DESCRIPTION, PRICE, COLOUR, BRAND
                FROM PRODUCTS
                WHERE P_ID = ?
            """, (field_value,))
            row = cursor.fetchone()
            if row:
                keys = ["P_ID", "NAME", "DESCRIPTION", "PRICE", "COLOUR", "BRAND"]
                return {"type": "product", "data": dict(zip(keys, row))}
            return {"error": f"Product ID {field_value} not found."}

        else:
            return {"error": "Invalid field name."}

    except sqlite3.Error as e:
        return {"error": str(e)}
    finally:
        conn.close()
