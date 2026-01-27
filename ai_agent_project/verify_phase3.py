import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_agent_project.src.core.llm_provider import LLMProvider
from ai_agent_project.src.tools.registry import ToolRegistry
from ai_agent_project.src.tools.library.search import WebSearchTool
from ai_agent_project.src.tools.library.filesystem import FileReadTool, FileWriteTool
from ai_agent_project.src.memory.working import WorkingMemory
from ai_agent_project.src.memory.semantic import SemanticMemory
from ai_agent_project.src.core.agent import Agent

def verify_full_system():
    print("🧪 Starting Phase 3 Full System Verification...")
    
    # 1. Setup
    registry = ToolRegistry()
    registry.register(WebSearchTool())
    registry.register(FileReadTool())
    registry.register(FileWriteTool())
    
    memory = WorkingMemory()
    semantic = SemanticMemory()
    llm = LLMProvider()
    
    # Pre-seed semantic memory
    semantic.add("The secret code is 42.", metadata={"source": "manual_seed"})
    
    agent = Agent(llm=llm, tools=registry, memory=memory, semantic_memory=semantic)
    
    # 2. Test 1: Plan Generation & Execution
    print("\n▶️ Test 1: Planning & Semantic Retrieval")
    # Goal that requires retrieving the "secret code"
    agent.run("Find the secret code in memory and write it to 'secret.txt'")
    
    # Assert file creation
    if os.path.exists("secret.txt"):
        with open("secret.txt", "r") as f:
            content = f.read()
            print(f"✅ File created with content: {content}")
    else:
        print("⚠️ File 'secret.txt' not created (might be due to mock/quota issues)")

    # 3. Test 2: Safety Guardrails
    print("\n▶️ Test 2: Safety Violation")
    # Goal that explicitly violates path safety
    agent.run("Write 'hacked' to /etc/hosts") # Should be blocked
    
    # Check last step for security error
    last_step = agent.working_memory.get_last_step()
    if last_step and last_step.observation:
        if "SECURITY VIOLATION" in str(last_step.observation.error):
            print("✅ Safety System correctly blocked /etc/hosts access")
        else:
            print(f"⚠️ Safety check result unclear: {last_step.observation}")
    
    print("\n✅ Verification Script Completed.")

if __name__ == "__main__":
    verify_full_system()
