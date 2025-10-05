from langchain_ollama.chat_models import ChatOllama
from langchain.schema import HumanMessage
from typing import Dict, Any
from src.agents.sql_node import sql_node

ollama_model = ChatOllama(model="gemma:2b")

def viewer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    if "messages" not in state:
        state["messages"] = []

    user_input = state.get("latest_input", "").strip()
    if not user_input:
        return state

    # Extract user_id from state (must be set by frontend)
    user_id = state.get("user_id")
    intent = state.get("intent")

    # Extract relevant id from user input
    import re
    id_match = re.search(r"\b\d+\b", user_input)
    id_value = id_match.group(0) if id_match else None

    if intent == "order":
        if not id_value:
            llm_response = ollama_model.invoke(
                "User is asking about order but no order_id was found. "
                "Politely ask the user to provide their order ID."
            )
            state["messages"].append({"role": "viewer_agent", "content": llm_response.content})
            return state

        # Fetch order details
        order_info = sql_node("order_id", id_value , user_id)

        prompt = f"""
        User asked: {user_input}
        Order info: {order_info}
        Provide a natural, helpful response. If the ID is invalid, ask politely to check.
        """
        llm_response = ollama_model.invoke(prompt)
        state["messages"].append({"role": "viewer_agent", "content": llm_response.content})

    elif intent == "product":
        if not id_value:
            llm_response = ollama_model.invoke(
                "User is asking about a product but no product_id was found. "
                "Politely ask the user to provide the product ID."
            )
            state["messages"].append({"role": "viewer_agent", "content": llm_response.content})
            return state

        # Fetch product details
        product_info = sql_node("product_id", id_value)
        prompt = f"""
        User asked: {user_input}
        Product info: {product_info}
        Provide a natural, helpful response. If the ID is invalid, ask politely to check.
        """
        llm_response = ollama_model.invoke(prompt)
        state["messages"].append({"role": "viewer_agent", "content": llm_response.content})

    else:
        state["messages"].append({"role": "viewer_agent", "content": "Sorry, I can only help with orders or products."})

    return state

