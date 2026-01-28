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
                "temperature": 0.0 
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
