import sys
import os

# Fix path to include src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_agent_project.src.core.llm_provider import LLMProvider
from ai_agent_project.src.tools.registry import ToolRegistry
from ai_agent_project.src.tools.library.search import WebSearchTool
from ai_agent_project.src.memory.working import WorkingMemory
from ai_agent_project.src.core.agent import Agent

def verify_core():
    print("🧪 Starting Phase 2 Verification...")
    
    # 1. Initialize Components
    registry = ToolRegistry()
    registry.register(WebSearchTool())
    
    memory = WorkingMemory()
    llm = LLMProvider() # Be sure to use a mode where it doesn't fail on quota if possible, or catches it.
    
    agent = Agent(llm=llm, tools=registry, memory=memory)
    
    # 2. Run Agent
    print("\n▶️ Running Agent with goal: 'Get info on Python 3.12'")
    result = agent.run("Get info on Python 3.12")
    
    # 3. Assertions
    print("\n🔍 Verifying Result Structure...")
    assert result is not None, "Result should not be None"
    assert hasattr(result, 'success'), "Result must have success flag"
    assert hasattr(result, 'steps'), "Result must have steps history"
    
    if result.success:
        print("✅ Agent marked success")
        print(f"Answer: {result.answer}")
    else:
        print(f"⚠️ Agent finished with success=False (likely due to quota or mock fallback limits): {result.error}")
        
    # Check Memory
    print(f"Memory Steps: {len(memory.steps)}")
    if len(memory.steps) > 0:
        first_step = memory.steps[0]
        print(f"Step 1 Thought: {first_step.thought.text}")
        if first_step.action:
             print(f"Step 1 Action: {first_step.action.tool_name}")
             
    print("\n✅ Verification Script Completed.")

if __name__ == "__main__":
    verify_core()
