from fastapi import APIRouter
from agents.viewer_agent import get_viewer_agent

router = APIRouter()
agent = get_viewer_agent()

@router.get("/query")
def query_db(q: str):
    """Query the DB using natural language"""
    result = agent.invoke(q)
    return {"query": q, "result": result["output"]}