from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from ai_agent_project.src.tools.base import Tool
from ai_agent_project.src.core.types import ToolOutput
from ddgs import DDGS
import requests
from bs4 import BeautifulSoup
import re

class WebSearchInput(BaseModel):
    query: str = Field(..., description="The search query")
    max_results: int = Field(default=3, description="Number of results to return")

class WebSearchTool(Tool):
    name = "web_search"
    description = "Search the internet for up-to-date information. Use this when you need current facts. Returns titles, links, snippets, and page content."
    input_schema = WebSearchInput

    def _fetch_page_content(self, url: str, timeout: int = 10) -> Optional[str]:
        """Fetch and clean text content from a URL."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove clutter
            for element in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
                element.decompose()
                
            text = soup.get_text(separator=' ', strip=True)
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Limit length
            return text[:2500] + "..." if len(text) > 2500 else text
        except Exception as e:
            # print(f"Failed to fetch {url}: {e}") # Reduce noise
            return None

    def execute(self, input_data: WebSearchInput) -> ToolOutput:
        query = input_data.query
        results = []
        
        try:
            with DDGS() as ddgs:
                # Get raw results
                raw_results = []
                for r in ddgs.text(query, max_results=input_data.max_results):
                    raw_results.append(r)
            
            # Enrich with page content
            enriched_results = []
            fetched_count = 0
            
            for res in raw_results:
                item = {
                    "title": res['title'],
                    "link": res['href'],
                    "snippet": res['body'],
                    "content": None
                }
                
                # Fetch content for top 2 results
                if fetched_count < 2:
                    content = self._fetch_page_content(res['href'])
                    if content:
                        item["content"] = content
                        fetched_count += 1
                
                enriched_results.append(item)
                
            if not enriched_results:
                 return ToolOutput(success=False, result="No results found.")

            return ToolOutput(success=True, result=enriched_results)

        except Exception as e:
            return ToolOutput(success=False, error=str(e))

