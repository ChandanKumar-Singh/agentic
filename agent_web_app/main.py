from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import json
from typing import List, Dict, Optional, Any

from agent_web_app.core.llm import LLMProvider
from agent_web_app.core.agent import Agent
from agent_web_app.core.session_manager import SessionManager

# Configuration
HISTORY_DIR = os.path.join(os.path.dirname(__file__), "history")
app = FastAPI()

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Initialize Services
session_manager = SessionManager(HISTORY_DIR)
llm = LLMProvider()

# --- Models ---
class ChatRequest(BaseModel):
    message: str
    search_mode: bool = False
    session_id: Optional[str] = None

class SessionCreate(BaseModel):
    name: str

# --- Endpoints ---

@app.on_event("startup")
async def startup_event():
    # SessionManager loads on init, so just a log here
    print(f"[Server] Startup. History Dir: {HISTORY_DIR}")

@app.post("/api/sessions")
async def create_session(session: SessionCreate):
    return session_manager.create_session(session.name)

@app.get("/api/sessions")
async def list_sessions():
    return session_manager.list_sessions()

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    sess = session_manager.get_session(session_id)
    if not sess:
        return {"error": "Session not found"}
    return sess

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open(os.path.join(static_dir, "index.html")) as f:
        return f.read()

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    query = request.message
    session_id = request.session_id
    
    # Store User Message
    if session_id:
        session_manager.add_message(session_id, "user", query)

    final_response_text = ""
    steps = []

    if request.search_mode:
        print("[Server] Search Mode ON. Initializing Agent...")
        # 1. Initialize Agent (New Tool Registry is auto-init inside)
        agent = Agent(llm)
        
        # 2. Run Agent Loop
        raw_result = agent.run(query)
        
        # 3. Refine with Llama3.1 (Synthesis Step)
        print("[Server] Refining answer with llama3.1:8b...")
        refine_prompt = f"""
        User Question: {query}
        
        Research Findings:
        {raw_result}
        
        Please provide a high-quality, professional final answer based on these findings.
        """
        final_answer = llm.generate(refine_prompt, model="llama3.1:8b")
        
        final_response_text = final_answer
        steps = agent.history
        
    else:
        print("[Server] Normal Chat Mode. Using phi3:latest...")
        response = llm.generate(query, model="phi3:latest")
        final_response_text = response
        steps = []

    # Store AI Response
    if session_id:
        session_manager.add_message(session_id, "ai", final_response_text)
        if steps:
             session_manager.add_message(session_id, "system", f"Steps: {json.dumps(steps)}")

    return {"response": final_response_text, "steps": steps}

if __name__ == "__main__":
    import uvicorn
    # Use environment variables for host/port if available
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
