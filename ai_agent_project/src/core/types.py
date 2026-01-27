from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class ToolInput(BaseModel):
    """Base class for tool input arguments."""
    pass

class ToolOutput(BaseModel):
    """Standardized output from any tool execution."""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class Action(BaseModel):
    """Represents an action the agent wants to take."""
    tool_name: str
    tool_args: Dict[str, Any]
    thought: Optional[str] = None

class Thought(BaseModel):
    """Represents the agent's reasoning process."""
    text: str
    plan: Optional[List[str]] = None
    criticism: Optional[str] = None
    is_final_answer: bool = False
    answer: Optional[str] = None
    action_name: Optional[str] = None
    action_input: Optional[Dict[str, Any]] = None

class Step(BaseModel):
    """A single step in the agent's execution history."""
    step_id: int
    thought: Thought
    action: Optional[Action] = None
    observation: Optional[ToolOutput] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class AgentResult(BaseModel):
    """Final result of an agent run."""
    success: bool
    answer: Optional[str] = None
    error: Optional[str] = None
    steps: List[Step] = []
    metadata: Dict[str, Any] = {}
