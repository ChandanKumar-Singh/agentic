from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import json
import asyncio
import uuid
from typing import List, Dict, Optional, Any

from agent_web_app.core.llm import LLMProvider
from agent_web_app.core.agent import Agent

# Persistent session storage
HISTORY_DIR = os.path.join(os.path.dirname(__file__), "history")
os.makedirs(HISTORY_DIR, exist_ok=True)

# Structure: { "session_id": { "name": "...", "messages": [...] } }
SESSIONS: Dict[str, Any] = {}

def save_session(session_id: str, data: dict):
    filepath = os.path.join(HISTORY_DIR, f"{session_id}.json")
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

def load_sessions():
    global SESSIONS
    print("[Server] Loading sessions from history...")
    for filename in os.listdir(HISTORY_DIR):
        if filename.endswith(".json"):
            session_id = filename[:-5]
            filepath = os.path.join(HISTORY_DIR, filename)
            try:
                with open(filepath, "r") as f:
                    SESSIONS[session_id] = json.load(f)
            except Exception as e:
                print(f"[Server] Failed to load session {session_id}: {e}")
    print(f"[Server] Loaded {len(SESSIONS)} sessions.")

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    load_sessions()

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

llm = LLMProvider()

class ChatRequest(BaseModel):
    message: str
    search_mode: bool = False
    session_id: Optional[str] = None

class SessionCreate(BaseModel):
    name: str

class SessionList(BaseModel):
    id: str
    name: str

@app.post("/api/sessions")
async def create_session(session: SessionCreate):
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {
        "name": session.name,
        "messages": []
    }
    save_session(session_id, SESSIONS[session_id])
    return {"id": session_id, "name": session.name}

@app.get("/api/sessions")
async def list_sessions():
    return [
        {"id": k, "name": v["name"]} 
        for k, v in SESSIONS.items()
    ]

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    if session_id not in SESSIONS:
        return {"error": "Session not found"}
    return SESSIONS[session_id]

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open(os.path.join(static_dir, "index.html")) as f:
        return f.read()

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    query = request.message
    session_id = request.session_id
    
    # Store User Message
    if session_id and session_id in SESSIONS:
        SESSIONS[session_id]["messages"].append({"role": "user", "content": query})
        save_session(session_id, SESSIONS[session_id])

    final_response_text = ""
    steps = []

    if request.search_mode:
        print("[Server] Search Mode ON. Initializing Agent...")
        # 1. Initialize Agent with Phi3 Latest
        agent = Agent(llm)
        
        # 2. Run Agent Loop
        # Agent uses Phi3 Latest to plan and Mistral to search/summarize
        raw_result = agent.run(query)
        
        # 3. Refine with Llama3.1
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
        # Direct chat with Phi3 Latest
        response = llm.generate(query, model="phi3:latest")
        final_response_text = response
        steps = []

    # Store AI Response
    if session_id and session_id in SESSIONS:
        SESSIONS[session_id]["messages"].append({"role": "ai", "content": final_response_text})
        if steps:
             SESSIONS[session_id]["messages"].append({"role": "system", "content": f"Steps: {json.dumps(steps)}"})
        save_session(session_id, SESSIONS[session_id])

    return {"response": final_response_text, "steps": steps}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
