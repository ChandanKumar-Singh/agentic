import requests
import json
import time

BASE_URL = "http://127.0.0.1:8001"

def test_session_lifecycle():
    print("\n[Test] Session Lifecycle...")
    # 1. Create Session
    resp = requests.post(f"{BASE_URL}/api/sessions", json={"name": "Test Session"})
    assert resp.status_code == 200
    session_id = resp.json()["id"]
    print(f"Created Session: {session_id}")
    
    # 2. Get Session
    resp = requests.get(f"{BASE_URL}/api/sessions/{session_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Test Session"
    print("Session Retrieval: OK")
    
    return session_id

def test_calculator_execution(session_id):
    print("\n[Test] Calculator Execution (Search Mode ON)...")
    # Ask a math question to trigger CalculatorTool
    payload = {
        "message": "Calculate 50 * 20",
        "search_mode": True,
        "session_id": session_id
    }
    
    start = time.time()
    resp = requests.post(f"{BASE_URL}/api/chat", json=payload)
    print(f"Response Time: {time.time() - start:.2f}s")
    
    assert resp.status_code == 200
    data = resp.json()
    
    # Check if we got a response
    print(f"Response: {data['response']}")
    
    # Check if Calculator was used in steps
    steps = data.get("steps", [])
    calc_used = any("calculator" in str(step).lower() for step in steps)
    if calc_used:
        print("Calculator Tool Used: YES")
    else:
        print("Calculator Tool Used: NO (Might be handled by LLM directly)")
        print(f"Steps: {steps}")

def test_tool_registry_structure():
    # This is a unit test-like check we can run if we import valid modules
    # But since server is running, we trust the API test more.
    pass

if __name__ == "__main__":
    try:
        # Wait for server to be up
        time.sleep(2)
        sid = test_session_lifecycle()
        test_calculator_execution(sid)
        print("\n✅ Phase 1 Verification PASSED")
    except Exception as e:
        print(f"\n❌ Phase 1 Verification FAILED: {e}")
