from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from typing import Annotated
from src.agents.router import router_node
from src.agents.viewer_node import viewer_node

class State(TypedDict):
    messages: list
    latest_input: str
    intent: str
    user_id: int
    current_order_id: str | None
    current_product_id: str | None

workflow = StateGraph(State)


# Conditional edges
workflow.add_node("router", router_node)
workflow.add_node("Viewer", viewer_node)
workflow.add_edge(START, "router")
workflow.add_edge("Viewer", END)  # After viewing order, go back to router


def router_selector(state):
    if state.get("intent") == "order":
        return "Viewer"
    return END

workflow.add_conditional_edges(
    "router",
    router_selector
)

    # Add more agents in the future
    # ("router", lambda s: s.get("intent") == "product", "ProductViewer"),

workflow = workflow.compile()

