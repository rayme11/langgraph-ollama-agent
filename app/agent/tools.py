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


# Export list of tools for graph binding
TOOLS = [get_weather, get_stock_quote]
