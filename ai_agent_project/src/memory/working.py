from typing import List, Dict, Any, Optional
from ai_agent_project.src.core.types import Step, Thought, Action, ToolOutput

class WorkingMemory:
    """
    Manages the short-term context for the agent.
    Stores the current goal, the history of steps (thoughts, actions, observations),
    and any temporary variables.
    """
    def __init__(self):
        self.goal: Optional[str] = None
        self.steps: List[Step] = []
        self.context: Dict[str, Any] = {}
        
    def initialize(self, goal: str):
        """Reset memory and set new goal."""
        self.clear()
        self.goal = goal
        
    def clear(self):
        """Clear all memory."""
        self.goal = None
        self.steps = []
        self.context = {}

    def add_step(self, step: Step):
        """Add a completed step to the history."""
        self.steps.append(step)
        
    def get_history(self) -> str:
        """Format the history as a string for LLM context."""
        if not self.steps:
            return "No previous steps."
            
        history_text = []
        for step in self.steps:
            history_text.append(f"Step {step.step_id}:")
            history_text.append(f"  Thought: {step.thought.text}")
            
            if step.action:
                history_text.append(f"  Action: {step.action.tool_name}")
                history_text.append(f"  Input: {step.action.tool_args}")
            
            if step.observation:
                status = "Success" if step.observation.success else "Failed"
                result = step.observation.result if step.observation.success else step.observation.error
                history_text.append(f"  Observation ({status}): {result}")
            
            history_text.append("-" * 20)
            
        return "\n".join(history_text)

    def get_last_step(self) -> Optional[Step]:
        if not self.steps:
            return None
        return self.steps[-1]
