import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8001"

def test_sessions():
    # 1. Create Session
    print("Creating session...")
    res = requests.post(f"{BASE_URL}/api/sessions", json={"name": "Test Session"})
    if res.status_code != 200:
        print(f"Failed to create session: {res.text}")
        sys.exit(1)
    
    data = res.json()
    session_id = data["id"]
    print(f"Session created: {session_id}")

    # 2. List Sessions
    print("Listing sessions...")
    res = requests.get(f"{BASE_URL}/api/sessions")
    sessions = res.json()
    found = any(s["id"] == session_id for s in sessions)
    if not found:
        print("Session not found in list!")
        sys.exit(1)
    print("Session found in list.")

    # 3. Chat
    print("Sending message...")
    chat_payload = {
        "message": "Hello, are you there?",
        "search_mode": False,
        "session_id": session_id
    }
    res = requests.post(f"{BASE_URL}/api/chat", json=chat_payload)
    if res.status_code != 200:
         print(f"Chat failed: {res.text}")
         sys.exit(1)
    print(f"Chat response: {res.json()['response']}")

    # 4. Get Session History
    print("Verifying history...")
    res = requests.get(f"{BASE_URL}/api/sessions/{session_id}")
    history = res.json()
    messages = history.get("messages", [])
    if len(messages) < 2: # User + AI
        print("History check failed: Not enough messages saved.")
        print(history)
        sys.exit(1)
    
    print("History verified.")
    print("ALL TESTS PASSED")

if __name__ == "__main__":
    test_sessions()
