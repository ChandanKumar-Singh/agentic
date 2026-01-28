import uuid
import threading
import time
import asyncio
import json
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel

from ai_agent_project.src.core.llm_provider import LLMProvider
from ai_agent_project.src.tools.registry import ToolRegistry
from ai_agent_project.src.tools.library.search import WebSearchTool
from ai_agent_project.src.tools.library.filesystem import FileWriteTool, FileReadTool
from ai_agent_project.src.memory.working import WorkingMemory
from ai_agent_project.src.memory.semantic import SemanticMemory
from ai_agent_project.src.core.agent import Agent
from ai_agent_project.src.core.types import AgentResult

from ai_agent_project.src.config.settings import settings

app = FastAPI(title="AI Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ask")
def ask_model(p: str):
    if not p:
        raise HTTPException(status_code=400, detail="Missing 'p' parameter")

    try:
        # Use existing LLMProvider for consistent behavior
        llm = LLMProvider() 
        response_content = llm.generate(p)

        return {
            "model": settings.MODEL_NAME,
            "prompt": p,
            "response": response_content
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Event System ---
class EventStream:
    def __init__(self):
        self.queue = asyncio.Queue()
    
    def put(self, event_type: str, data: Any):
        # We need to run this in the event loop, but it might be called from a thread
        try:
            loop = asyncio.get_running_loop()
            loop.call_soon_threadsafe(self.queue.put_nowait, {"event": event_type, "data": data})
        except RuntimeError:
             # If no running loop (rare in this setup), try to create one or just use run_coroutine_threadsafe
            pass 

    async def iterator(self):
        while True:
            item = await self.queue.get()
            if item["event"] == "DONE":
                break
            yield {"event": item["event"], "data": json.dumps(item["data"])}

class AgentRun:
    def __init__(self, run_id: str, goal: str):
        self.run_id = run_id
        self.goal = goal
        self.status = "initializing"
        self.result: Optional[AgentResult] = None
        self.start_time = time.time()
        self.stream = EventStream()
        
        # Initialize Components
        self.llm = LLMProvider()
        self.registry = ToolRegistry()
        self.registry.register(WebSearchTool())
        self.registry.register(FileWriteTool())
        self.registry.register(FileReadTool())
        self.memory = WorkingMemory()
        self.semantic = SemanticMemory()
        
        self.agent = Agent(
            llm=self.llm, 
            tools=self.registry, 
            memory=self.memory, 
            semantic_memory=self.semantic
        )

    def execute(self):
        self.status = "running"
        
        # Define callbacks that push to the async queue
        def callback_handler(event_name, data):
             # Helper to bridge thread -> async queue
             # Since 'execute' runs in a thread, we need to access the main event loop
             # But 'EventStream.put' handles loop discovery.
             # Wait, EventStream.put uses 'get_running_loop', which works if called from async context OR 
             # if we have a handle to the loop. 
             # Let's fix EventStream.put to robustly handle cross-thread putting.
             loop = asyncio.new_event_loop() 
             # Actually, in FastAPI, there is a main loop. We should capture it or use run_coroutine_threadsafe.
             # Better approach: Pass the loop to AgentRun or use a thread-safe queue wrapper.
             pass

        # Robust cross-thread callback
        loop = asyncio.get_event_loop_policy().get_event_loop() 
        # Note: getting the loop like this from a thread might be tricky.
        # Let's rely on `loop.call_soon_threadsafe` but we need the MAIN loop.
        # We will capture the loop in the `start_run` method (which is async)
        
    def execute_with_loop(self, loop):
        self.status = "running"
        
        callbacks = {
            "on_start": lambda d: loop.call_soon_threadsafe(self.stream.queue.put_nowait, {"event": "start", "data": d}),
            "on_step": lambda d: loop.call_soon_threadsafe(self.stream.queue.put_nowait, {"event": "step", "data": d}),
            "on_thought": lambda d: loop.call_soon_threadsafe(self.stream.queue.put_nowait, {"event": "thought", "data": d}),
            "on_action": lambda d: loop.call_soon_threadsafe(self.stream.queue.put_nowait, {"event": "action", "data": d}),
            "on_observation": lambda d: loop.call_soon_threadsafe(self.stream.queue.put_nowait, {"event": "observation", "data": d}),
            "on_subtask_complete": lambda d: loop.call_soon_threadsafe(self.stream.queue.put_nowait, {"event": "subtask_complete", "data": d}),
        }

        try:
            self.result = self.agent.run(self.goal, callbacks=callbacks)
            self.status = "completed" if self.result.success else "failed"
            loop.call_soon_threadsafe(self.stream.queue.put_nowait, {"event": "result", "data": {"answer": self.result.answer, "error": self.result.error}})
        except Exception as e:
            self.status = "error"
            loop.call_soon_threadsafe(self.stream.queue.put_nowait, {"event": "error", "data": str(e)})
        finally:
            loop.call_soon_threadsafe(self.stream.queue.put_nowait, {"event": "DONE", "data": {}})


class RunManager:
    def __init__(self):
        self.runs: Dict[str, AgentRun] = {}

    def start_run(self, goal: str) -> str:
        run_id = str(uuid.uuid4())
        run = AgentRun(run_id, goal)
        self.runs[run_id] = run
        
        # Capture current event loop (FastAPI's loop)
        loop = asyncio.get_running_loop()
        
        # Start in background thread, passing the loop
        thread = threading.Thread(target=run.execute_with_loop, args=(loop,))
        thread.start()
        
        return run_id

    def get_run(self, run_id: str) -> Optional[AgentRun]:
        return self.runs.get(run_id)

    def list_runs(self):
        return [
            {
                "run_id": r.run_id, 
                "goal": r.goal, 
                "status": r.status,
                "steps_count": len(r.memory.steps),
                "timestamp": r.start_time
            }
            for r in self.runs.values()
        ]

manager = RunManager()

class RunRequest(BaseModel):
    goal: str

@app.post("/api/run")
async def start_run(request: RunRequest):
    run_id = manager.start_run(request.goal)
    return {"run_id": run_id, "status": "started"}

@app.get("/api/runs")
async def list_runs():
    return manager.list_runs()

@app.get("/api/run/{run_id}/stream")
async def stream_run(run_id: str, request: Request):
    run = manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    return EventSourceResponse(run.stream.iterator())

# Keep legacy endpoint for backward compatibility/debugging
@app.get("/api/run/{run_id}")
async def get_run_details(run_id: str):
    run = manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    plan_data = []
    if run.agent.planner and run.agent.planner.plan:
        plan_data = [t.dict() for t in run.agent.planner.plan.subtasks]

    return {
        "run_id": run.run_id,
        "goal": run.goal,
        "status": run.status,
        "steps": [s.dict() for s in run.memory.steps],
        "final_answer": run.result.answer if run.result else None,
        "error": run.result.error if run.result else None,
        "plan": plan_data
    }

import os
from fastapi.responses import FileResponse
static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

@app.get("/chat")
async def chat_page():
    return FileResponse(os.path.join(static_path, "chat.html"))

app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
