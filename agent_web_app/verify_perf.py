import requests
import json
import time

BASE_URL = "http://127.0.0.1:8001"

def test_performance():
    print("\n[Test] Performance Check...")
    # 1. Create Session
    requests.post(f"{BASE_URL}/api/sessions", json={"name": "Perf Test"})
    
    # 2. Hard Calc (Should be instant)
    start = time.time()
    resp = requests.post(f"{BASE_URL}/api/chat", json={
        "message": "Calculate 123 * 456",
        "search_mode": True
    })
    duration = time.time() - start
    print(f"Calc Duration: {duration:.2f}s")
    if duration > 5:
        print("❌ Calc too slow! (Did it use LLM?)")
    else:
        print("✅ Calc FAST")

    # 3. Web Search (Should be fast - no 2nd LLM)
    start = time.time()
    resp = requests.post(f"{BASE_URL}/api/chat", json={
        "message": "Who is the current CEO of Microsoft?",
        "search_mode": True
    })
    duration = time.time() - start
    print(f"Search Duration: {duration:.2f}s")
    
    data = resp.json()
    print(f"Response: {data['response'][:100]}...")
    
    # 4. Check for 'mistral' usage in tools (Indirect check)
    # We can't easily check server logs from here but duration is the key.

if __name__ == "__main__":
    time.sleep(2) # Wait for server
    try:
        test_performance()
    except Exception as e:
        print(f"Error: {e}")
