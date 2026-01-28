import sys
import os

# Ensure parent directory is in path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from agent_web_app.core.llm import LLMProvider
from agent_web_app.core.agent import Agent

def test_image_search():
    print("Initializing LLM...")
    llm = LLMProvider()
    agent = Agent(llm)
    
    query = "show me tajmaal image"
    print(f"Running Agent with query: '{query}'")
    
    # Run agent
    try:
        result = agent.run(query)
        print("\n--- Final Result ---")
        print(result)
        
        if "![" in result and "](" in result:
             print("\nSUCCESS: Image markdown found.")
        else:
             print("\nFAILURE: No image markdown found.")
             
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_image_search()
