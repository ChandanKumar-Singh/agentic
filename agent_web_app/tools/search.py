from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
import re
from agent_web_app.core.llm import LLMProvider

class WebSearchTool:
    name = "web_search"
    description = "Search the web for real-time information. Returns a summary."
    
    def __init__(self, llm_provider):
        self.llm = llm_provider

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

    def execute(self, query: str, max_results: int = 3) -> str:
        print(f"[Tool:WebSearch] Searching for: {query}")
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
        for res in results:
            if fetched >= 2: break
            text = self._fetch_page_content(res['href'])
            if text:
                content_context += f"Source: {res['title']}\nURL: {res['href']}\nContent: {text}\n\n"
                fetched += 1
        
        # Fallback to snippets
        if not content_context:
             for res in results:
                 content_context += f"Source: {res['title']}\nSnippet: {res['body']}\n\n"

        # Summarize using Mistral
        prompt = f"""
        User Query: {query}
        
        Search Results:
        {content_context}
        
        Summarize the above findings to answer the user's query directly and concisely.
        """
        
        print("[Tool:WebSearch] Summarizing with mistral:latest...")
        summary = self.llm.generate(prompt, model="mistral:latest")
        return summary
