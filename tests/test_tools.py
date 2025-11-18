from __future__ import annotations

import pytest

from app.agent import tools as tools_module


class DummySettings:
    openweather_api_key = "DUMMY_WEATHER_KEY"
    alphavantage_api_key = "DUMMY_STOCK_KEY"


def fake_get_settings():
    # Override settings to ensure API keys are "present" during tests
    return DummySettings()


@pytest.fixture(autouse=True)
def patch_settings(monkeypatch):
    # Patch get_settings used inside tools.py
    monkeypatch.setattr("app.agent.tools.get_settings", fake_get_settings)
    yield


def test_get_weather_success(monkeypatch):
    # Arrange: fake HTTP response
    def fake_http_get_json(url, params, timeout=15):
        return {
            "main": {"temp": 23.5, "humidity": 40},
            "wind": {"speed": 5.0},
            "weather": [{"description": "clear sky"}],
        }

    monkeypatch.setattr(tools_module, "_http_get_json", fake_http_get_json)

    # Act
    result = tools_module.get_weather.run(
        tool_input={"city": "Austin,US", "units": "metric"}
    )

    # Assert
    assert result["city"] == "Austin,US"
    assert result["temp"] == 23.5
    assert result["humidity"] == 40
    assert result["condition"] == "clear sky"
    assert result["source"] == "openweathermap"


def test_get_stock_quote_success(monkeypatch):
    # Arrange
    def fake_http_get_json(url, params, timeout=15):
        return {
            "Global Quote": {
                "05. price": "100.00",
                "08. previous close": "98.00",
                "09. change": "2.00",
                "10. change percent": "2.04%",
            }
        }

    monkeypatch.setattr(tools_module, "_http_get_json", fake_http_get_json)

    # Act
    result = tools_module.get_stock_quote.run(tool_input={"symbol": "AAPL"})

    # Assert
    assert result["symbol"] == "AAPL"
    assert result["price"] == 100.0
    assert result["previous_close"] == 98.0
    assert result["change"] == 2.0
    assert result["percent_change"] == "2.04%"
    assert pytest.approx(result["percent_change_float"], rel=1e-3) == 2.04


def test_get_stock_quote_missing_key(monkeypatch):
    # Arrange: simulate missing API key by patching settings
    class NoKeySettings:
        openweather_api_key = "DUMMY"
        alphavantage_api_key = ""

    def fake_no_key_settings():
        return NoKeySettings()

    monkeypatch.setattr("app.agent.tools.get_settings", fake_no_key_settings)

    # Act
    monkeypatch.setattr(tools_module, "settings", NoKeySettings())
    result = tools_module.get_stock_quote.run(tool_input={"symbol": "AAPL"})

    # Assert
    assert "error" in result
    assert result["error"]["code"] == "missing_api_key"
