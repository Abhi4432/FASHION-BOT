import sqlite3
import hashlib
import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from src.agents.workflow import workflow  # make sure agents folder has __init__.py

# DB path (adjust according to your folder structure)
DB_PATH = os.path.abspath("data/fashion_ai.db") 

app = FastAPI(title="Fashion AI Backend")

# -------------------------------
# Schemas
# -------------------------------
class Message(BaseModel):
    role: str
    content: str

class StateRequest(BaseModel):
    messages: List[Message]
    user_id: int

class StateResponse(BaseModel):
    messages: List[Message]

class LoginRequest(BaseModel):
    username_or_email: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    msg: str
    user_id: int = None

# -------------------------------
# Routes
# -------------------------------
@app.get("/")
async def root():
    return {"msg": "Fashion AI Backend is running 🚀"}

@app.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    """
    Check username OR email against stored hashed password.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT USER_ID, PASSWORD FROM USERS WHERE USERNAME=? OR EMAIL=?",
            (req.username_or_email, req.username_or_email)
        )
        row = cursor.fetchone()
        if not row:
            return {"success": False, "msg": "User not found"}
        user_id, stored_hash = row

        # Hash input password same as in seed
        input_hash = hashlib.sha256(req.password.encode("utf-8")).hexdigest()

        if input_hash == stored_hash:
            return {"success": True, "msg": "Login successful", "user_id": user_id}
        else:
            return {"success": False, "msg": "Incorrect password"}
    finally:
        conn.close()

@app.post("/chat", response_model=StateResponse)
async def chat_endpoint(req: StateRequest):
    """
    Post conversation messages to LangGraph workflow and return updated messages.
    """
    state = {
        "messages": [m.dict() for m in req.messages],
        "user_id": req.user_id  # Store as string for consistency
    }
    user_messages = [m for m in req.messages if m.role == "user"]
    state["latest_input"] = user_messages[-1].content if user_messages else ""
    updated_state = workflow.invoke(state)
    print(updated_state , "\n")
    def to_message(m):
        if isinstance(m, dict):
            return Message(**m)
        return Message(role=getattr(m, "role", "user"), content=getattr(m, "content", ""))
    return {
        "messages": [to_message(m) for m in updated_state["messages"]]
    }


