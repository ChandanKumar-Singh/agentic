import os
import json
import uuid
from typing import Dict, Any, List, Optional

class SessionManager:
    def __init__(self, history_dir: str):
        self.history_dir = history_dir
        self.sessions: Dict[str, Any] = {}
        os.makedirs(self.history_dir, exist_ok=True)
        self.load_sessions()

    def load_sessions(self):
        print("[SessionManager] Loading sessions from history...")
        self.sessions = {}
        for filename in os.listdir(self.history_dir):
            if filename.endswith(".json"):
                session_id = filename[:-5]
                filepath = os.path.join(self.history_dir, filename)
                try:
                    with open(filepath, "r") as f:
                        self.sessions[session_id] = json.load(f)
                except Exception as e:
                    print(f"[SessionManager] Failed to load session {session_id}: {e}")
        print(f"[SessionManager] Loaded {len(self.sessions)} sessions.")

    def save_session(self, session_id: str):
        if session_id not in self.sessions:
            return
        filepath = os.path.join(self.history_dir, f"{session_id}.json")
        with open(filepath, "w") as f:
            json.dump(self.sessions[session_id], f, indent=2)

    def create_session(self, name: str) -> Dict[str, str]:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "name": name,
            "messages": []
        }
        self.save_session(session_id)
        return {"id": session_id, "name": name}

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.sessions.get(session_id)

    def list_sessions(self) -> List[Dict[str, str]]:
        return [{"id": k, "name": v["name"]} for k, v in self.sessions.items()]

    def add_message(self, session_id: str, role: str, content: str):
        if session_id in self.sessions:
            self.sessions[session_id]["messages"].append({"role": role, "content": content})
            self.save_session(session_id)
