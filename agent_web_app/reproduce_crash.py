import sys
import os

# Ensure parent directory is in path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from agent_web_app.core.llm import LLMProvider
from agent_web_app.core.agent import Agent

def reproduce():
    print("Initializing Agent...")
    llm = LLMProvider()
    agent = Agent(llm)
    
    query = "Calculate 50 * 20"
    print(f"Running query: {query}")
    try:
        result = agent.run(query)
        print("Result:", result)
    except Exception as e:
        print("Crashed:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reproduce()
