from typing import List, Dict
from pydantic import BaseModel, Field
from ai_agent_project.src.tools.base import Tool
from ai_agent_project.src.core.types import ToolOutput

class WebSearchInput(BaseModel):
    query: str = Field(..., description="The search query")
    max_results: int = Field(default=3, description="Number of results to return")

class WebSearchTool(Tool):
    name = "web_search"
    description = "Search the internet for up-to-date information. Use this when you need current facts."
    input_schema = WebSearchInput

    def execute(self, input_data: WebSearchInput) -> ToolOutput:
        # NOTE: For this project template, we'll use a Mock implementation 
        # to ensure it runs without an API key immediately. 
        # In production, swap with Google/Bing/SerpAPI.
        
        query = input_data.query.lower()
        mock_results = []

        if "python" in query:
             mock_results = [
                {"title": "Python 3.12 Release Notes", "snippet": "Python 3.12 introduces flexible f-strings and better error messages.", "link": "https://docs.python.org/3.12/"},
                {"title": "Real Python: What's new in 3.12", "snippet": "Detailed breakdown of the new GIL features and performance boosts.", "link": "https://realpython.com/"}
            ]
        elif "agent" in query:
             mock_results = [
                {"title": "Agentic AI Overview", "snippet": "Autonomous agents are the next frontier of AI.", "link": "https://ai-news.com/agents"},
                {"title": "Building ReAct Agents", "snippet": "How to implement reasoning loops with LLMs.", "link": "https://arxiv.org/"}
            ]
        else:
             mock_results = [
                {"title": f"Results for {input_data.query}", "snippet": "Generic placeholder search result 1.", "link": "http://example.com/1"},
                {"title": f"More on {input_data.query}", "snippet": "Generic placeholder search result 2.", "link": "http://example.com/2"}
            ]

        return ToolOutput(
            success=True, 
            result=mock_results[:input_data.max_results]
        )
