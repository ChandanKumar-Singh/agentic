from abc import ABC, abstractmethod
from typing import Type, Dict, Any
from pydantic import BaseModel
from ai_agent_project.src.core.types import ToolInput, ToolOutput

class Tool(ABC):
    """Abstract base class for all tools"""
    
    name: str = "base_tool"
    description: str = "Base tool"
    input_schema: Type[BaseModel]

    @abstractmethod
    def execute(self, input_data: BaseModel) -> ToolOutput:
        """Execute the tool logic"""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert to LLM-friendly format (JSON Schema)"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.input_schema.model_json_schema()
        }
