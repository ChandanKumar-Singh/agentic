import requests
import os
import json

class LLMProvider:
    """Wrapper for Ollama API with dynamic model support."""
    
    def __init__(self, default_model="phi3:latest", host="http://192.168.1.13:11434"):
        self.default_model = default_model
        self.host = os.getenv("OLLAMA_HOST", host)
        self.base_url = f"{self.host}/api/chat"

    def generate(self, prompt: str, system_prompt: str = "You are a helpful AI assistant.", model: str = None) -> str:
        """
        Generate text using a specific model.
        
        Args:
            prompt: User prompt
            system_prompt: System instruction
            model: Optional model override. If None, uses default_model.
        """
        target_model = model or self.default_model
        
        payload = {
            "model": target_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_ctx": 2048,
                "num_predict": 300,
                "top_p": 0.9
            }
        }
        
        try:
            print(f"[LLM] Calling {target_model}...")
            response = requests.post(self.base_url, json=payload)
            response.raise_for_status()
            return response.json()["message"]["content"]
        except Exception as e:
            print(f"[LLM] Error calling {target_model}: {e}")
            return f"Error: {str(e)}"

    async def generate_async(self, prompt: str, system_prompt: str = "You are a helpful AI assistant.", model: str = None) -> str:
        """Async version of generate using thread pool."""
        import asyncio
        from functools import partial
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            partial(self.generate, prompt, system_prompt, model)
        )
