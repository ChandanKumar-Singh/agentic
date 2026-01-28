from ddgs import DDGS
import requests
from bs4 import BeautifulSoup
import re
from agent_web_app.core.llm import LLMProvider
from agent_web_app.core.tool import Tool

class WebSearchTool(Tool):
    name = "web_search"
    description = "Search the web for real-time information. Returns a summary."
    
    def __init__(self, llm_provider=None):
        # llm_provider is kept for signature compatibility but not used
        pass

    def _fetch_page_content(self, url: str, timeout: int = 10):
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            for el in soup(["script", "style", "nav", "footer"]):
                el.decompose()
            text = soup.get_text(separator=' ', strip=True)
            text = re.sub(r'\s+', ' ', text).strip()
            return text[:2500]
        except:
            return None

    async def execute(self, query: str, max_results: int = 3) -> str:
        import asyncio
        from functools import partial
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(cached_search, query, max_results))

from functools import lru_cache

@lru_cache(maxsize=100)
def cached_search(query: str, max_results: int = 3) -> str:
    print(f"[Tool:WebSearch] Searching for: {query} (Cache Miss)")
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(r)
    except Exception as e:
        return f"Search failed: {e}"

    if not results:
        return "No results found."

    # Fetch content
    content_context = ""
    fetched = 0
    # Note: _fetch_page_content assumes self. Refactor to standalone or keep simple snippets.
    # For speed (Phase 2), snippets are often enough and much faster than fetching full pages.
    # Let's rely on snippets first as per Plan "Return raw snippets".
    
    for res in results:
        # content_context += f"Source: {res['title']}\nURL: {res['href']}\nContent: ...\n\n"
        # Using body snippet provided by DDGS to avoid network fetches per page
        content_context += f"Source: {res['title']}\nSnippet: {res['body']}\n\n"
    
    print("[Tool:WebSearch] Returning raw results.")
    return content_context

    # def _sync_execute(self, query: str, max_results: int = 3) -> str:
    #    ... deleted ...

