import sqlite3
from typing import Dict, Any, Optional
# Assuming DB_PATH is correctly defined elsewhere (e.g., in db.config)
from db.config import DB_PATH

# Update signature to include mode and limit
def sql_node(relevant_data: Dict[str, Any], user_id: Optional[int] = None, mode: str = 'detail', limit: int = 1) -> Dict[str, Any]:
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        order_id = relevant_data.get("order_id")
        product_id = relevant_data.get("product_id")

        # --- MODE 3: RECOMMENDATION LOOKUP (FIXED: Using LIKE instead of MATCH) --- 
        if mode == 'recommendation':
            keywords = relevant_data.get('search_keywords', [])
            if not keywords:
                return {"error": "No keywords provided for recommendation search."}
            
            # Use standard SQL LIKE operator since MATCH requires FTS table
            # We construct a WHERE clause that searches for any of the keywords in the SEARCH_TEXT column
            
            # Example: WHERE SEARCH_TEXT LIKE '%kurti%' OR SEARCH_TEXT LIKE '%red%'
            like_conditions = [f"SEARCH_TEXT LIKE ?" for _ in keywords]
            where_clause = " OR ".join(like_conditions)
            
            # Prepare parameters: wrap each keyword with wildcards
            params = [f"%{keyword}%" for keyword in keywords]

            query = f"""
                SELECT P_ID, NAME, PRICE, COLOUR, BRAND, IMG, DESCRIPTION
                FROM PRODUCTS
                WHERE {where_clause}
                ORDER BY AVG_RATING DESC 
                LIMIT ?
            """
            
            # Append the limit parameter to the list of search parameters
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
                
            if not rows:
                return {"error": "We couldn't find any recommendations matching your criteria."}

            keys = ["P_ID", "NAME", "PRICE", "COLOUR", "BRAND", "IMG", "DESCRIPTION"]
            
            recommendations = []
            for row in rows:
                recommendations.append(dict(zip(keys, row)))

            return {"type": "recommendation", "recommendations": recommendations}


        # --- MODE 1: ORDER LOOKUP (if order_id exists) ---
        if order_id and mode != 'product':
            # ... (Existing order lookup logic remains the same) ...
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
                return {"error": f"No order found for order_id {order_id} and user {user_id}."}

            keys = [
                "order_id", "product_id", "user_id", "status", "order_date",
                "shipping_date", "delivery_date", "amount",
                "name", "price", "brand", "colour", "img", "description"
            ]
            return {"type": "order", **dict(zip(keys, row))}


        # --- MODE 2: PRODUCT DETAIL LOOKUP (fallback) ---
        # Build dynamic search filters
        filters, params = [], []
        search_fields = [
            "product_id", "name", "brand", "colour", "fabric",
            "occasion", "print_pattern", "top_type", "sleeve_length", "description"
        ]

        if product_id:
            filters.append("P_ID = ?")
            params.append(product_id)
        else:
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
        if conn:
            conn.close()


