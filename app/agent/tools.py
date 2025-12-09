# We’ll add real tools (HTTP via requests: stocks/weather) in Step 2–3.
from __future__ import annotations
import os
import requests
from typing import Optional, TypedDict

from langchain.tools import tool
from app.config import get_settings
from app.agent.sports_tools import (
    get_sports_odds,
    get_team_form,
    get_player_form,
)


settings = get_settings()

# ---------- HTTP helpers (plain functions) ----------
def _http_get_json(url: str, params: dict, timeout: int = 15) -> dict:
    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()

# ---------- Weather ----------
@tool("get_weather", return_direct=False)
def get_weather(city: str, units: str = "metric") -> dict:
    """
    Get current weather for a city using OpenWeatherMap.
    Args:
        city: e.g., "Austin,US" or "Austin"
        units: "metric" or "imperial"
    Returns:
        dict with temperature, humidity, conditions, wind
    """
    api_key = settings.openweather_api_key
    if not api_key:
        return {"error": "Missing OPENWEATHER_API_KEY in environment."}

    try:
        data = _http_get_json(
            "https://api.openweathermap.org/data/2.5/weather",
            {"q": city, "appid": api_key, "units": units},
        )
        main = data.get("main", {})
        wind = data.get("wind", {})
        weather = (data.get("weather") or [{}])[0]
        return {
            "city": city,
            "temp": main.get("temp"),
            "humidity": main.get("humidity"),
            "condition": weather.get("description"),
            "wind_speed": wind.get("speed"),
            "units": units,
            "source": "openweathermap",
        }
    except Exception as e:
        return {"error": f"weather_fetch_failed: {e}"}

# ---------- Stocks ----------
@tool("get_stock_quote", return_direct=False)
def get_stock_quote(symbol: str) -> dict:
    """
    Get latest stock quote using Alpha Vantage GLOBAL_QUOTE.

    Args:
        symbol: e.g., "AAPL"
    Returns:
        dict with:
          - symbol
          - price
          - previous_close
          - change
          - percent_change (string, e.g. '0.56%')
          - percent_change_float (float, e.g. 0.56)
          - source
        or a dict with an "error" field.
    """
    api_key = settings.alphavantage_api_key
    if not api_key:
        return {
            "error": {
                "code": "missing_api_key",
                "message": "Missing ALPHAVANTAGE_API_KEY in environment."
            }
        }

    try:
        data = _http_get_json(
            "https://www.alphavantage.co/query",
            {"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": api_key},
        )
        quote = data.get("Global Quote", {})
        if not quote:
            return {
                "error": {
                    "code": "no_quote",
                    "message": f"No quote found for symbol '{symbol}'.",
                    "raw_response": data,
                }
            }

        def to_float(x: Optional[str]) -> Optional[float]:
            try:
                return float(x) if x is not None else None
            except Exception:
                return None

        price = to_float(quote.get("05. price"))
        prev_close = to_float(quote.get("08. previous close"))
        change = to_float(quote.get("09. change"))
        pct_str = quote.get("10. change percent")  # e.g. "0.56%"

        pct_float: Optional[float] = None
        if isinstance(pct_str, str) and pct_str.endswith("%"):
            try:
                pct_float = float(pct_str.rstrip("%"))
            except Exception:
                pct_float = None

        return {
            "symbol": symbol.upper(),
            "price": price,
            "previous_close": prev_close,
            "change": change,
            "percent_change": pct_str,
            "percent_change_float": pct_float,
            "source": "alpha_vantage",
        }
    except Exception as e:
        return {
            "error": {
                "code": "stock_fetch_failed",
                "message": f"Failed to fetch stock data for symbol '{symbol}': {e!r}",
            }
        }


# ---------- “Advisor” prompt helper ----------
def stock_risk_hint() -> str:
    """
    Hint text used by the LLM when giving stock suggestions.

    Rubric (based on intraday % change vs previous close):
      - Low risk:   price is stable or slightly down (between -1% and +1%)
      - Medium risk: moderate move (between -3% and -1% or between +1% and +3%)
      - High risk:  large move (less than -3% or greater than +3%)

    Guidance:
      - Use the tool output fields: price, previous_close, change, percent_change.
      - Explain briefly why you chose the risk level.
      - Always remind the user this is NOT financial advice.
    """
    return (
        "Use this rubric for risk levels, based on intraday percent change vs previous close:\n"
        "- Low risk: price change between -1% and +1% (stable or slightly down/up)\n"
        "- Medium risk: price change between -3% and -1% OR between +1% and +3%\n"
        "- High risk: price change < -3% OR > +3%\n\n"
        "Base your suggestion on the tool fields (price, previous_close, change, percent_change). "
        "Explain your reasoning briefly and clearly, and always remind the user it is not financial advice."
    )
    
@tool("get_news", return_direct=False)
def get_news(category: str = "general", query: Optional[str] = None) -> dict:
    """
    Fetch the latest news headlines using NewsAPI.

    Args:
        category: One of 'business', 'entertainment', 'general', 'health',
                  'science', 'sports', or 'technology'. Default: 'general'.
        query: Optional free-text search query, e.g., 'AI', 'NVIDIA', 'World Cup'.

    Returns:
        dict with:
          - category
          - query
          - articles: list of {title, description, url, source, published_at}
          - source: 'newsapi'
        or an 'error' dict.
    """
    settings = get_settings()
    api_key = settings.news_api_key
    if not api_key:
        return {
            "error": {
                "code": "missing_news_api_key",
                "message": "NEWS_API_KEY is not set in the environment.",
            }
        }

    base_url = settings.news_api_base_url
    params = {
        "apiKey": api_key,
        "country": "us",  # adjust for your locale if needed
        "category": category,
        "pageSize": 5,
    }
    # If query is given, use 'everything' endpoint instead
    try:
        if query:
            url = f"{base_url}/everything"
            params = {
                "apiKey": api_key,
                "q": query,
                "pageSize": 5,
                "sortBy": "publishedAt",
                "language": "en",
            }
        else:
            url = f"{base_url}/top-headlines"

        data = _http_get_json(url, params)

        status = data.get("status")
        if status != "ok":
            return {
                "error": {
                    "code": "news_api_error",
                    "message": f"News API returned non-ok status: {status}",
                    "raw": data,
                }
            }

        articles_raw = data.get("articles", [])
        articles = []
        for a in articles_raw:
            articles.append(
                {
                    "title": a.get("title"),
                    "description": a.get("description"),
                    "url": a.get("url"),
                    "source": (a.get("source") or {}).get("name"),
                    "published_at": a.get("publishedAt"),
                }
            )

        if not articles:
            return {
                "error": {
                    "code": "no_news_found",
                    "message": "No news articles found for the given category/query.",
                }
            }

        return {
            "category": category,
            "query": query,
            "articles": articles,
            "source": "newsapi",
        }
    except Exception as e:
        return {
            "error": {
                "code": "news_fetch_failed",
                "message": f"Failed to fetch news: {e!r}",
            }
        }

@tool("web_search", return_direct=False)
def web_search(query: str) -> dict:
    """
    Perform a real web search using the Tavily Search API.

    Requires:
      - WEB_SEARCH_ENABLED=true
      - WEB_SEARCH_API_KEY=<your Tavily key>

    Args:
        query: Search query text.

    Returns:
        dict:
            - query: the original query
            - results: list of {title, snippet, url}
            - source: "tavily"
        or:
            - error: { code, message }
    """
    settings = get_settings()

    # Check feature flag
    if not settings.web_search_enabled:
        return {
            "error": {
                "code": "web_search_disabled",
                "message": "Web search is disabled. Set WEB_SEARCH_ENABLED=true in the environment.",
            }
        }

    api_key = settings.web_search_api_key
    if not api_key:
        return {
            "error": {
                "code": "missing_web_search_key",
                "message": "WEB_SEARCH_API_KEY is missing. Obtain a key from https://tavily.com",
            }
        }

    if not query or not query.strip():
        return {
            "error": {
                "code": "empty_query",
                "message": "web_search query must not be empty.",
            }
        }

    # Tavily Search endpoint
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "max_results": 5,
        "include_answer": False,
    }

    try:
        import requests

        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        tavily_results = data.get("results", [])
        results = []
        for r in tavily_results:
            results.append(
                {
                    "title": r.get("title"),
                    "snippet": r.get("snippet") or r.get("content"),
                    "url": r.get("url"),
                }
            )

        if not results:
            return {
                "query": query,
                "results": [],
                "source": "tavily",
                "warning": "No results found.",
            }

        return {
            "query": query,
            "results": results,
            "source": "tavily",
        }

    except Exception as e:
        return {
            "error": {
                "code": "web_search_failed",
                "message": f"Web search failed: {e!r}",
            }
        }



# Export list of tools for graph binding
TOOLS = [
    get_weather,
    get_stock_quote,
    get_news,
    web_search,
    get_sports_odds,
    get_team_form,
    get_player_form,
]
