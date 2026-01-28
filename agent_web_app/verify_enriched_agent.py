import sys
import os

# Ensure parent directory is in path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from agent_web_app.core.llm import LLMProvider
from agent_web_app.core.agent import Agent

def test_calculator():
    print("\n--- Testing Calculator ---")
    llm = LLMProvider()
    agent = Agent(llm)
    
    query = "What is 153 * 19?"
    print(f"Goal: {query}")
    result = agent.run(query)
    print(f"Result: {result}")
    
    if "2907" in str(result) or "2,907" in str(result):
        print("SUCCESS: Calculator worked.")
    else:
        print("FAILURE: Calculator result incorrect.")

def test_wikipedia():
    print("\n--- Testing Wikipedia ---")
    llm = LLMProvider()
    agent = Agent(llm)
    
    query = "Who built the Taj Mahal?"
    print(f"Goal: {query}")
    result = agent.run(query)
    print(f"Result: {result}")
    
    if "Shah Jahan" in str(result):
        print("SUCCESS: Wikipedia worked.")
    else:
        print("FAILURE: Wikipedia result incorrect.")

if __name__ == "__main__":
    test_calculator()
    test_wikipedia()
