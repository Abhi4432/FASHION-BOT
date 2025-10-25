# src/agents/billing_node.py

from typing import Dict, Any
import sqlite3
from datetime import date, timedelta
# Assuming DB_PATH is available from a config file
# If you don't have a db.config, ensure DB_PATH is defined here or imported from main.py
try:
    from db.config import DB_PATH 
except ImportError:
    # Fallback/Mock DB_PATH if config is not available
    DB_PATH = "data/fashion_ai.db" 

def billing_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handles the order placement logic after a recommendation confirmation.
    - Inserts a new order into the database.
    - Provides the order_id and amount back to the user.
    """
    relevant_data = state.get("relevant_data", {})
    # Note: user_id is an int in State, ensure it's handled correctly
    user_id = state.get("user_id") 

    product_id = relevant_data.get('product_id')
    price = relevant_data.get('price')
    product_name = relevant_data.get('name', 'recommended product')
    amount = relevant_data.get('price') # Assume price is the final amount

    if not product_id or not amount:
        state["error_msg"] = (
            "Cannot place order: Missing product ID or price. "
            "Please start a new product search."
        )
        return state

    conn = None
    new_order_id = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # --- 1. Calculate dates and insert order ---
        order_date = date.today().isoformat()
        # Mock dates: Shipping tomorrow, Delivery in 4 days
        shipping_date = (date.today() + timedelta(days=1)).isoformat()
        delivery_date = (date.today() + timedelta(days=4)).isoformat()
        
        # Ensure price is a float for DB insertion
        amount_float = float(amount)

        insert_query = """
            INSERT INTO ORDERS (PRODUCT_ID, USER_ID, PRODUCT_DESCRIPTION, ORDER_DATE, SHIPPING_DATE, DELIVERY_DATE, AMOUNT, STATUS)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'ordered')
        """
        cursor.execute(insert_query, (
            product_id, 
            user_id, 
            product_name, 
            order_date, 
            shipping_date, 
            delivery_date, 
            amount_float
        ))
        conn.commit()
        
        # Get the ID of the newly created order
        new_order_id = cursor.lastrowid

        # --- 2. Generate final success message ---
        msg = (
            f"✅ **Order Placed Successfully!** Thank you for confirming your purchase of the **{product_name}**."
            f"\n\nYour new **Order ID is: {new_order_id}**."
            f" The total amount charged is ${amount_float:.2f}."
            f" It's expected to deliver on {delivery_date}."
        )

        state["messages"].append({"role": "billing_agent", "content": msg})
        
        # --- 3. Update relevant_data for potential follow-up ---
        # Clear product-specific search terms, but keep the new order_id
        keys_to_clear = ['product_id', 'name', 'price', 'brand', 'colour', 'img', 'description', 'type']
        for key in keys_to_clear:
            relevant_data.pop(key, None)
            
        relevant_data['order_id'] = str(new_order_id)
        relevant_data['amount'] = amount_float
        relevant_data['status'] = 'ordered'
        
        state["relevant_data"] = relevant_data
        state["error_msg"] = None

    except sqlite3.Error as e:
        state["error_msg"] = f"Database error during order placement: {e}"
    except Exception as e:
        state["error_msg"] = f"An unexpected error occurred during billing: {e}"
    finally:
        if conn:
            conn.close()
            
    return state