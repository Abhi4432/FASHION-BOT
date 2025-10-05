from langchain_ollama.chat_models import ChatOllama
from langchain.schema import HumanMessage
from typing import Dict, Any


ollama_model = ChatOllama(model="gemma:2b")

def router_node(state: Dict[str, Any]) -> Dict[str, Any]:
    user_input = state.get("latest_input", "").strip()
    if not user_input:
        return {"intent": "none"}

    # Take last 2 messages only for context
    recent_context = "\n".join(
        [f"{m['role']}: {m['content']}" for m in state.get("messages", [])[-2:]]
    )

    routing_prompt = f"""
    Conversation so far:
    {recent_context}

    User query: "{user_input}"

    Decide the intent:
    - "order" if user wants order details, status, tracking, etc.
    - "product" if user wants product details, description, or features.
    - "recommendation" if user asks for similar items or suggestions.
    - "none" otherwise.

    IMPORTANT: Return only one word: order, product, recommendation, or none.
    """

    llm_response = ollama_model.invoke(routing_prompt)
    raw_intent = llm_response.content.strip().lower()

    # Post-process to guarantee valid output
    if "order" in raw_intent:
        intent = "order"
    elif "product" in raw_intent:
        intent = "product"
    elif "recommendation" in raw_intent:
        intent = "recommendation"
    else:
        intent = "none"

    state["intent"] = intent
    return state


