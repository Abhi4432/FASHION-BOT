from langchain_ollama.chat_models import ChatOllama
from typing import Dict, Any

ollama_model = ChatOllama(model="gemma:2b")

def error_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gracefully handles any errors raised from other nodes.
    Generates a polite, context-aware response.
    """
    error_text = state.get("error_msg", "An unknown error occurred.")
    user_input = state.get("latest_input", "")

    prompt = f"""
    The user said: "{user_input}".
    An error occurred: "{error_text}".
    Respond politely, apologize if needed, and suggest a next step or correction.
    """
    response = ollama_model.invoke(prompt)

    state["messages"].append({
        "role": "error_agent",
        "content": response.content
    })
    state["error_msg"] = None
    return state
