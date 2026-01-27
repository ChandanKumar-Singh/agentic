from typing import Dict, List, Optional
from ai_agent_project.src.tools.base import Tool

class ToolRegistry:
    """Central repository for available tools"""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        """Register a new tool"""
        self._tools[tool.name] = tool
        # print(f"DEBUG: Registered tool '{tool.name}'")

    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self._tools.get(name)

    def list_tools(self) -> List[Tool]:
        """Return all registered tools"""
        return list(self._tools.values())
    
    def to_llm_format(self) -> List[Dict]:
        """Return list of tools explicitly formatted for LLM consumption"""
        return [t.to_dict() for t in self._tools.values()]
