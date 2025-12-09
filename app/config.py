# -*- coding: utf-8 -*-
from pydantic import BaseModel
from functools import lru_cache
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
    # --- Core LLM & infra ---
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openweather_api_key: Optional[str] = os.getenv("OPENWEATHER_API_KEY")
    alphavantage_api_key: Optional[str] = os.getenv("ALPHAVANTAGE_API_KEY")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # --- News API (NewsGenie) ---
    news_api_key: Optional[str] = os.getenv("NEWS_API_KEY")
    news_api_base_url: str = os.getenv(
        "NEWS_API_BASE_URL",
        "https://newsapi.org/v2",
    )

    # --- Web Search (Tavily) ---
    web_search_enabled: bool = os.getenv("WEB_SEARCH_ENABLED", "true").lower() == "true"
    web_search_api_key: Optional[str] = os.getenv("WEB_SEARCH_API_KEY")
    web_search_engine_id: Optional[str] = os.getenv("WEB_SEARCH_ENGINE_ID")

    # --- RAG (News embeddings store) ---
    rag_news_db_path: str = os.getenv("RAG_NEWS_DB_PATH", "./rag_news_db")
    openai_embeddings_model: str = os.getenv(
        "OPENAI_EMBEDDINGS_MODEL",
        "text-embedding-3-small",
    )

    # --- Sports Betting: Odds & Stats ---

    # The Odds API
    odds_api_key: Optional[str] = os.getenv("ODDS_API_KEY")
    odds_api_base_url: str = os.getenv(
        "ODDS_API_BASE_URL",
        "https://api.the-odds-api.com/v4",
    )

    # Sportsdata.io
    sportsdata_api_key: Optional[str] = os.getenv("SPORTSDATA_API_KEY")

    sportsdata_nba_base_url: str = os.getenv(
        "SPORTSDATA_NBA_BASE_URL",
        "https://api.sportsdata.io/v3/nba",
    )
    sportsdata_nfl_base_url: str = os.getenv(
        "SPORTSDATA_NFL_BASE_URL",
        "https://api.sportsdata.io/v3/nfl",
    )
    sportsdata_mlb_base_url: str = os.getenv(
        "SPORTSDATA_MLB_BASE_URL",
        "https://api.sportsdata.io/v3/mlb",
    )
    sportsdata_nhl_base_url: str = os.getenv(
        "SPORTSDATA_NHL_BASE_URL",
        "https://api.sportsdata.io/v3/nhl",
    )
    sportsdata_cbb_base_url: str = os.getenv(
        "SPORTSDATA_CBB_BASE_URL",
        "https://api.sportsdata.io/v3/cbb",
    )
    sportsdata_soccer_base_url: str = os.getenv(
        "SPORTSDATA_SOCCER_BASE_URL",
        "https://api.sportsdata.io/v3/soccer",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
