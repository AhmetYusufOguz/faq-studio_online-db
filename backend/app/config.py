import os
import logging
from dotenv import load_dotenv

# Logging config
LOG_LEVEL = logging.INFO   # DEBUG / INFO / WARNING

load_dotenv()

class Settings:
    EMBED_MODEL = os.getenv("EMBED_MODEL", "bge-m3")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    SIM_THRESHOLD = float(os.getenv("SIM_THRESHOLD", "0.75"))
    JSON_PATH = os.getenv("JSON_PATH", "/app/data/questions.json")
    CATEGORIES_PATH = os.getenv("CATEGORIES_PATH", "/app/data/categories.json")

settings = Settings()