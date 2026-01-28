import wikipedia
from agent_web_app.core.tool import Tool

class WikipediaTool(Tool):
    name = "wikipedia"
    description = "Search Wikipedia for summaries. Use this for general knowledge queries."

    async def execute(self, query: str) -> str:
        import asyncio
        from functools import partial
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(cached_wikipedia, query))

from functools import lru_cache

@lru_cache(maxsize=100)
def cached_wikipedia(query: str) -> str:
    print(f"[Tool:Wikipedia] Searching for: {query} (Cache Miss)")
    try:
        # Limit to 2 sentences to keep context concise
        summary = wikipedia.summary(query, sentences=2)
        return summary
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Ambiguous term. Options: {e.options[:5]}"
    except wikipedia.exceptions.PageError:
        return "Page not found."
    except Exception as e:
        return f"Wikipedia error: {str(e)}"
