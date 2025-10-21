# src/agents/viewer_node.py

from langchain_ollama.chat_models import ChatOllama
from typing import Dict, Any
from src.agents.sql_node import sql_node 
import re 

ollama_model = ChatOllama(model="gemma:2b")

def viewer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    if "messages" not in state:
        state["messages"] = []

    relevant_data = state.get("relevant_data", {})
    user_id = state.get("user_id")
    user_input = state.get("latest_input", "").strip().lower()

    # If no relevant data available, politely ask
    if 'order_id' not in relevant_data and 'product_id' not in relevant_data:
        msg = "Could you please specify your order ID or describe the product?"
        state["messages"].append({"role": "viewer_agent", "content": msg})
        return state

    # Check if necessary data is already in state (Data Reuse)
    needs_sql = not any(field in relevant_data for field in ['status', 'delivery_date', 'shipping_date', 'img', 'price'])
    
    sql_result = {}
    if needs_sql:
        # Run SQL lookup (will only fetch if needed)
        sql_result = sql_node(relevant_data, user_id)
        # ... (error handling remains the same)
        if "error" in sql_result:
            state["messages"].append({"role": "viewer_agent", "content": f"⚠️ {sql_result['error']}"})
            state["error_msg"] = sql_result["error"]
            return state

    # --- Merge SQL result into relevant data (Update State) ---
    for key, val in sql_result.items():
        if val is not None and str(val).strip() != "":
            relevant_data[key] = val
            
    state["relevant_data"] = relevant_data 

    # --- Generate Natural Response ---
    
    # 1. SPECIAL CASE: Image Request 
    if ('image' in user_input or 'img' in user_input) and 'img' in relevant_data:
        img_url = relevant_data['img']
        # ONLY return the image URL
        response_content = img_url 
        state["messages"].append({"role": "viewer_agent", "content": response_content})
        state["error_msg"] = None
        return state
    
    # 2. General Query Response (Use LLM with full context)
    relevant_data_text = "\n".join([f"{k}: {v}" for k, v in relevant_data.items()]) 
    
    viewing_prompt = f"""
    The user asked: "{state.get('latest_input', '')}"

    Full Available Context (Use ONLY this information to construct your response):
    {relevant_data_text}

    Task: Respond concisely and naturally based ONLY on the user's latest query. 
    
    RULES:
    1. **Conciseness:** Provide the specific requested value (e.g., status, date, price) in one or two short, natural sentences.
    2. **Anti-Hallucination:** DO NOT mention any fields that the user did not ask for. DO NOT state that data is unavailable if it is present in the context above.
    3. **Focus:** If the user asks for 'status', give the status. If they ask for 'delivery date', give the delivery date.

    Example: 
    User: "what is the order status"
    Response: "Your order is currently {relevant_data.get('status')}."

    Example:
    User: "what is the delivery date"
    Response: "The estimated delivery date is {relevant_data.get('delivery_date')}."
    """

    llm_response = ollama_model.invoke(viewing_prompt)
    state["messages"].append({"role": "viewer_agent", "content": llm_response.content})
    state["error_msg"] = None

    return state


