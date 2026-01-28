from abc import ABC, abstractmethod
from typing import Dict, Any, List

class Tool(ABC):
    """Abstract base class for all tools."""
    name: str
    description: str

    @abstractmethod
    def execute(self, **kwargs) -> str:
        pass

class ToolRegistry:
    """Registry to manage and discover tools."""
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        if not tool.name:
            raise ValueError("Tool name cannot be empty")
        self._tools[tool.name] = tool
        print(f"[Registry] Registered tool: {tool.name}")

    def get(self, name: str) -> Tool:
        return self._tools.get(name)

    def list_tools(self) -> List[Tool]:
        return list(self._tools.values())

    def get_prompt_text(self) -> str:
        """Generates the tools section for the prompt."""
        text = "Available Tools:\n"
        for tool in self._tools.values():
            text += f"- {tool.name}: {tool.description}\n"
        return text
