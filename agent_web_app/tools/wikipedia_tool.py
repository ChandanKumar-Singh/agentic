import wikipedia

class WikipediaTool:
    name = "wikipedia"
    description = "Search Wikipedia for summaries. Use this for general knowledge queries."

    def execute(self, query: str) -> str:
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
