from langchain_ollama.chat_models import ChatOllama
from typing import Dict, Any

ollama_model = ChatOllama(model="gemma:2b")

def none_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handles vague or unclear queries politely.
    """
    user_input = state.get("latest_input", "")
    prompt = f"""
    The user said: "{user_input}".
    You could not determine intent.
    Politely ask for clarification or suggest possible things they can do
    (like checking an order, viewing a product, or exploring recommendations).
    """
    response = ollama_model.invoke(prompt)

    state["messages"].append({
        "role": "none_agent",
        "content": response.content
    })
    return state
