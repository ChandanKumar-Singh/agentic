from ddgs import DDGS
from ollama import Client
import argparse
import requests
from bs4 import BeautifulSoup

def search_web(query, max_results=3):
    """Search the web using DuckDuckGo."""
    print(f"Searching for: {query}...")
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(r)
    except Exception as e:
        print(f"Error during search: {e}")
        return []
    return results

def fetch_page_content(url, timeout=10):
    """Fetch and extract text from a URL."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script, style, nav, footer, and other clutter
        for element in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            element.decompose()
            
        text = soup.get_text(separator=' ', strip=True)
        # Clean up excessive whitespace
        import re
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Limit text length (approx 2000 chars per source)
        return text[:2000] + "..." if len(text) > 2000 else text
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None

def summarize_results(query, results, model_name="deepseek-r1:1.5b", host="http://192.168.1.13:11434"):
    """Summarize search results using Ollama."""
    print(f"Summarizing with model: {model_name}...")
    
    if not results:
        return "No results found to summarize."

    # Prepare context from results
    context_text = ""
    
    # Try to fetch content for the TOP 2 results
    fetched_count = 0
    for res in results:
        if fetched_count >= 2:
            break
            
        url = res['href']
        print(f"Fetching detailed content from: {url}")
        page_content = fetch_page_content(url)
        if page_content:
            context_text += f"Content from {res['title']} ({url}):\n{page_content}\n\n"
            fetched_count += 1
    
    # Add snippets for all results as backup
    for i, res in enumerate(results, 1):
        context_text += f"---\nSource {i} Snippet: {res['title']}\nURL: {res['href']}\nSnippet: {res['body']}\n---\n\n"

    prompt = f"""
    You are a helpful research assistant. 
    The user asked: "{query}"
    
    Here is the information gathered from the web (including page content and search snippets):
    {context_text}
    
    Please provide a direct and concise answer to the user's question based ONLY on the provided text.
    If the answer is explicitly mentioned (like a specific time, date, or fact), quote it.
    """

    try:
        client = Client(host=host)
        response = client.chat(
            model=model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"]
    except Exception as e:
        return f"Error during summarization: {e}"

def main():
    parser = argparse.ArgumentParser(description="Web Search & Summarization Agent")
    parser.add_argument("query", nargs="*", help="The search query")
    parser.add_argument("--model", default="deepseek-r1:1.5b", help="Ollama model to use")
    parser.add_argument("--host", default="http://192.168.1.13:11434", help="Ollama host URL")
    
    args = parser.parse_args()
    
    if not args.query:
        # Interactive mode if no query provided
        query = input("Enter your search query: ")
    else:
        query = " ".join(args.query)

    if not query.strip():
        print("Empty query. Exiting.")
        return

    # 1. Search
    results = search_web(query)
    
    if results:
        print(f"\nFound {len(results)} results. Generating summary...\n")
        
        # 2. Summarize
        summary = summarize_results(query, results, model_name=args.model, host=args.host)
        
        print("-" * 40)
        print("SUMMARY")
        print("-" * 40)
        print(summary)
        print("-" * 40)
        print("\nSources:")
        for r in results:
            print(f"- {r['title']}: {r['href']}")
    else:
        print("No results found.")

if __name__ == "__main__":
    main()
