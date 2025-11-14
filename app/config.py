from pydantic import BaseModel
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openweather_api_key: str | None = os.getenv("OPENWEATHER_API_KEY")
    alphavantage_api_key: str | None = os.getenv("ALPHAVANTAGE_API_KEY")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

@lru_cache
def get_settings() -> Settings:
    return Settings()
