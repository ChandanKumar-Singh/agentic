from ddgs import DDGS
from agent_web_app.core.tool import Tool

class ImageSearchTool(Tool):
    name = "image_search"
    description = "Search for images. Input: query string. Returns: markdown image links."

    def execute(self, query: str, max_results: int = 3) -> str:
        print(f"[Tool:ImageSearch] Searching images for: {query}")
        images = []
        try:
            with DDGS() as ddgs:
                results = ddgs.images(query, max_results=max_results)
                for r in results:
                    images.append(f"![{r['title']}]({r['image']})")
        except Exception as e:
            return f"Image search failed: {e}"

        if not images:
            return "No images found."
        
        return "\n".join(images)
