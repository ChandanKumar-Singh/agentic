import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    MODEL_NAME = os.getenv("AGENT_MODEL_NAME", "gpt-4-turbo-preview")
    SIDE_MODEL_NAME = os.getenv("SIDE_MODEL_NAME", "gemini-pro")
    MAX_LOOPS = int(os.getenv("MAX_LOOPS", "15"))
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MEMORY_PATH = os.path.join(BASE_DIR, "data", "memory")
    SAFETY_CONFIG_PATH = os.path.join(BASE_DIR, "config", "safety_policy.yaml")

    # Guardrails
    BLOCKED_TOOLS = ["system_shell", "delete_root"]

settings = Settings()
