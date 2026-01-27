import sys
import os

# Ensure we can import from the project root (parent directory)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_agent_project.src.core.llm_provider import LLMProvider
from ai_agent_project.src.tools.registry import ToolRegistry
from ai_agent_project.src.tools.library.search import WebSearchTool
from ai_agent_project.src.tools.library.filesystem import FileWriteTool, FileReadTool
from ai_agent_project.src.memory.working import WorkingMemory
from ai_agent_project.src.core.agent import Agent

def main():
    print("Initializing AI Agent System...")
    
    # 1. Setup Tools
    registry = ToolRegistry()
    registry.register(WebSearchTool())
    registry.register(FileWriteTool())
    registry.register(FileReadTool())
    
    # 2. Setup Components
    llm = LLMProvider()
    memory = WorkingMemory()
    
    # 3. Create Agent
    agent = Agent(llm=llm, tools=registry, memory=memory)
    
    # 4. Run with a default goal if none provided
    if len(sys.argv) > 1:
        goal = " ".join(sys.argv[1:])
    else:
        goal = "Research recent python 3.12 features and save a short summary to 'python_summary.txt'"
    
    result = agent.run(goal)
    
    if result.success:
        print("\n✅ SUCCESS!")
        print(f"Result: {result.answer}")
    else:
        print("\n❌ FAILURE")
        print(f"Error: {result.error}")

if __name__ == "__main__":
    main()
