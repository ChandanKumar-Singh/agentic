from typing import List, Dict, Any, Optional
import json
import os
import time
import requests
from openai import OpenAI
import google.genai as genai
from ai_agent_project.src.config.settings import settings

class LLMProvider:
    """Wrapper for LLM API"""
    
    def __init__(self):
        # Determine mode based on configuration
        self.mode = "mock"
        self.provider = "none"
        
        # Check explicit overrides or keys
        if "llama" in settings.MODEL_NAME.lower() or "qwen" in settings.MODEL_NAME.lower():
            print(f"Ollama model detected: {settings.MODEL_NAME}")
            self.mode = "api"
            self.provider = "ollama"
            self.base_url = settings.OLLAMA_BASE_URL
        
        elif "gemini" in settings.MODEL_NAME.lower():
            if settings.GEMINI_API_KEY:
                print(f"API Key found for Gemini. Using model: {settings.MODEL_NAME}")
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.gemini_model = genai.GenerativeModel(settings.MODEL_NAME)
                self.mode = "api"
                self.provider = "gemini"
            else:
                 print("⚠️ WARNING: Gemini model selected but GEMINI_API_KEY not found. Fallback to Mock.")
        
        elif settings.OPENAI_API_KEY:
            print("API Key found. Running in API mode. API Key: ", settings.OPENAI_API_KEY)
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.mode = "api"
            self.provider = "openai"
        else:
            print("⚠️ WARNING: No API Key found. Running in MOCK mode.")

    def generate(self, prompt: str, system_prompt: str = "You are a helpful AI assistant.") -> str:
        if self.mode == "mock":
            return self._mock_generate(prompt)
        
        try:
            if self.provider == "ollama":
                payload = {
                    "model": settings.MODEL_NAME,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.0
                    }
                }
                response = requests.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                return response.json()["message"]["content"]

            elif self.provider == "gemini":
                # Gemini doesn't strictly separate system prompt in the same way for basic calls, 
                # but we can prepend it.
                full_prompt = f"{system_prompt}\n\n{prompt}"
                response = self.gemini_model.generate_content(full_prompt)
                return response.text

            elif self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=settings.MODEL_NAME,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0
                )
                return response.choices[0].message.content
                
        except Exception as e:
            print(f"⚠️ API Call Failed ({str(e)}). Falling back to MOCK response.")
            return self._mock_generate(prompt)

    def _mock_generate(self, prompt: str) -> str:
        """Simulate agent behavior for demo purposes"""
        time.sleep(1) # Simulate thinking
        
        # simple heuristic based on history in prompt
        if "Action: web_search" not in prompt:
            return """Thought: I need to start by researching the topic. I will use the web search tool.
Action: web_search
Action Input: {"query": "current topic", "max_results": 2}"""
        
        elif "Action: file_write" not in prompt:
            return """Thought: I have gathered the information. Now I will save it to a file.
Action: file_write
Action Input: {"filepath": "result.txt", "content": "This is a summary of the research found via the agent.", "mode": "w"}"""
        
        else:
            return """Thought: I have completed the task operations.
Final Answer: I have researched the topic and saved the results to result.txt"""
