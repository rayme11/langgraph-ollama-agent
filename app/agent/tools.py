# We’ll add real tools (HTTP via requests: stocks/weather) in Step 2–3.
from __future__ import annotations
import os
import requests
from typing import Optional, TypedDict

from langchain.tools import tool
from app.config import get_settings

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
        dict with price, change, percent_change, previous_close
    """
    api_key = settings.alphavantage_api_key
    if not api_key:
        return {"error": "Missing ALPHAVANTAGE_API_KEY in environment."}

    try:
        data = _http_get_json(
            "https://www.alphavantage.co/query",
            {"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": api_key},
        )
        quote = data.get("Global Quote", {})
        if not quote:
            return {"error": f"No quote found for {symbol}. Response: {data}"}

        def to_float(x: Optional[str]) -> Optional[float]:
            try:
                return float(x) if x is not None else None
            except Exception:
                return None

        price = to_float(quote.get("05. price"))
        prev_close = to_float(quote.get("08. previous close"))
        change = to_float(quote.get("09. change"))
        pct = quote.get("10. change percent")  # e.g., "0.56%"

        return {
            "symbol": symbol.upper(),
            "price": price,
            "previous_close": prev_close,
            "change": change,
            "percent_change": pct,
            "source": "alpha_vantage",
        }
    except Exception as e:
        return {"error": f"stock_fetch_failed: {e}"}

# ---------- “Advisor” prompt helper ----------
def stock_risk_hint() -> str:
    """
    A small helper string the LLM can use when giving advice.
    We keep advice simple & transparent; the LLM will combine with real quote data.
    """
    return (
        "Provide an informal buy/sell/hold suggestion categorized as Low/Medium/High risk. "
        "Base it on intraday change vs previous close, and remind users this is not financial advice."
    )

# Export list of tools for graph binding
TOOLS = [get_weather, get_stock_quote]
