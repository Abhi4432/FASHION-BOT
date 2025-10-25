# src/agents/workflow.py

from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from typing import Optional, Dict, Any
import os # NEW IMPORT for file system operations

# Import all nodes
from src.agents.router_node import router_node
from src.agents.viewer_node import viewer_node
from src.agents.recommendation_node import recommendation_node 
from src.agents.billing_node import billing_node        # NEW IMPORT
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
workflow.add_node("RecommendationHandler", recommendation_node) 
workflow.add_node("BillingHandler", billing_node)        # NEW NODE
workflow.add_node("ErrorHandler", error_node)
workflow.add_node("NoneHandler", none_node)

# Edges for basic flow
workflow.add_edge(START, "router")

# Conditional routing based on intent
def router_selector(state: State):
    intent = state.get("intent")
    if intent == "details":
        return "Viewer"
    elif intent == "recommendation":
        return "RecommendationHandler"
    elif intent == "billing":                            # NEW CONDITION
        return "BillingHandler"
    elif intent == "none":
        return "NoneHandler"
    else:
        return "NoneHandler"  # fallback

workflow.add_conditional_edges(
    "router",
    router_selector
)

# Define outcome functions for handlers (all route to Error on failure, END on success)
def handler_outcome(state: State):
    if state.get("error_msg"):
        return "ErrorHandler"
    else:
        return END

# Conditional edges from handlers
workflow.add_conditional_edges("Viewer", handler_outcome)
workflow.add_conditional_edges("RecommendationHandler", handler_outcome)
workflow.add_conditional_edges("BillingHandler", handler_outcome) # NEW EDGES

# Edges from Error and None handlers
workflow.add_edge("ErrorHandler", END)
workflow.add_edge("NoneHandler", END)

# Compile graph
workflow = workflow.compile()
app = workflow # Alias for clarity

# ------------------------------------------------------------------
# CODE TO PRINT/SAVE GRAPH (PNG File)
# ------------------------------------------------------------------
try:
    # 1. Ensure the output directory exists
    if not os.path.exists('graphs'):
        os.makedirs('graphs')
        
    # 2. Use the .draw() method to save the graph to a file
    # This requires 'graphviz' to be installed (pip install langgraph[draw])
    app.get_graph().draw("graphs/fashion_ai_workflow.png", prog="dot")
    print("\n" + "="*50)
    print("✅ LangGraph workflow graph saved to graphs/fashion_ai_workflow.png")
    print("="*50 + "\n")
except ImportError:
    print("\n" + "="*50)
    print("Warning: 'graphviz' or 'pygraphviz' not installed. Cannot draw PNG file.")
    print("Install with: pip install langgraph[draw]")
    print("="*50 + "\n")
except Exception as e:
    print(f"Warning: Could not draw graph image. Error: {e}")

# The compiled graph 'app' is returned/used by main.py