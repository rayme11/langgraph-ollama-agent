from pydantic import BaseModel
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    # Existing fields
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openweather_api_key: str | None = os.getenv("OPENWEATHER_API_KEY")
    alphavantage_api_key: str | None = os.getenv("ALPHAVANTAGE_API_KEY")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # NEW — for NewsAPI (https://newsapi.org/)
    news_api_key: str | None = os.getenv("NEWS_API_KEY")
    news_api_base_url: str = os.getenv("NEWS_API_BASE_URL", "https://newsapi.org/v2")

    # NEW — for Tavily Web Search (recommended)
    web_search_enabled: bool = os.getenv("WEB_SEARCH_ENABLED", "true").lower() == "true"
    web_search_api_key: str | None = os.getenv("WEB_SEARCH_API_KEY")

    # Optional Google CSE (not required for Tavily)
    web_search_engine_id: str | None = os.getenv("WEB_SEARCH_ENGINE_ID")

@lru_cache
def get_settings() -> Settings:
    return Settings()
