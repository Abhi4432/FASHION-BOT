from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from typing import Annotated, Optional, Dict, Any

# Import all nodes
from src.agents.router_node import router_node
from src.agents.viewer_node import viewer_node
from src.agents.error_node import error_node
from src.agents.none_node import none_node


# -------------------------------
# Define shared State type
# -------------------------------
class State(TypedDict):
    messages: list
    latest_input: str
    intent: str
    user_id: int
    relevant_data: Dict[str, Any]
    error_msg: Optional[str]


# -------------------------------
# Build graph
# -------------------------------
workflow = StateGraph(State)

# Add all nodes
workflow.add_node("router", router_node)
workflow.add_node("Viewer", viewer_node)
workflow.add_node("ErrorHandler", error_node)
workflow.add_node("NoneHandler", none_node)

# Edges for basic flow
workflow.add_edge(START, "router")

# Conditional routing based on intent
def router_selector(state: State):
    intent = state.get("intent")
    if intent == "details":
        return "Viewer"
    elif intent == "none":
        return "NoneHandler"
    else:
        return "NoneHandler"  # fallback

workflow.add_conditional_edges(
    "router",
    router_selector
)

# From viewer → error handler if something went wrong
def viewer_outcome(state: State):
    if state.get("error_msg"):
        return "ErrorHandler"
    else:
        return END

workflow.add_conditional_edges(
    "Viewer",
    viewer_outcome
)

# From error or none → END
workflow.add_edge("ErrorHandler", END)
workflow.add_edge("NoneHandler", END)

workflow = workflow.compile()

print("✅ Workflow compiled successfully.")
