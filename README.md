
---

````markdown
# 🧠 NewsGenie — AI-Powered News, Weather, Stocks & Sports Betting Assistant

NewsGenie is an end-to-end **agentic AI system** built with **LangGraph**, **LangChain**, **FastAPI**, **Streamlit**, **SQLite**, and real-time APIs for:

- 📰 News  
- 🌦️ Weather  
- 📈 Stocks  
- 🔎 Web Search  
- 🏀🏈⚽ Sports Betting Analysis & Recommendations  

It works with both **OpenAI** and **local LLMs via Ollama** and provides:

- Tool-using AI agents  
- Live data fetching  
- Sports betting recommendations (LOW / MEDIUM / HIGH / NOT RECOMMENDED)  
- Persistent conversation memory  

---

## 🔧 Technology Stack

<div align="left">

<img src="https://img.shields.io/badge/Python-3.9+-blue?logo=python" />
<img src="https://img.shields.io/badge/LangChain-Framework-2C4F7C" />
<img src="https://img.shields.io/badge/LangGraph-Agents-8A2BE2" />
<img src="https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white" />
<img src="https://img.shields.io/badge/Streamlit-UI-FF4B4B?logo=streamlit&logoColor=white" />
<img src="https://img.shields.io/badge/DB-SQLite-07405E?logo=sqlite&logoColor=white" />
<img src="https://img.shields.io/badge/LLM-Ollama-000000?logo=ollama&logoColor=white" />
<img src="https://img.shields.io/badge/LLM-OpenAI-412991?logo=openai&logoColor=white" />
<img src="https://img.shields.io/badge/Weather-OpenWeatherMap-orange" />
<img src="https://img.shields.io/badge/Stocks-AlphaVantage-yellow" />
<img src="https://img.shields.io/badge/News-NewsAPI-blue" />
<img src="https://img.shields.io/badge/Search-Tavily-purple" />
<img src="https://img.shields.io/badge/Odds-The_Odds_API-brown" />
<img src="https://img.shields.io/badge/Stats-Sportsdata.io-green" />

</div>

---

## 🎥 Live Demo

![NewsGenie Demo](https://raw.githubusercontent.com/rayme11/langgraph-ollama-agent/main/docs/assets/demo_newsgenie.gif)

---

## 🖼 Architecture Diagram

![NewsGenie Architecture](https://raw.githubusercontent.com/rayme11/langgraph-ollama-agent/main/docs/assets/newsgenie_architecture.png)

---

# 📘 Table of Contents

1. Overview  
2. Requirements  
3. Installation  
4. Environment Variables  
5. Project Structure  
6. Tools Overview  
7. Sports Betting System  
8. LangGraph Agent Architecture  
9. FastAPI API Usage  
10. Streamlit UI  
11. Sports Betting Examples  
12. Testing & Smoke Tests  
13. Troubleshooting  
14. Disclaimer  

---

# 1. Overview

NewsGenie is a **multi-tool reasoning AI agent** that:

- Detects user intent  
- Calls the correct API automatically  
- Uses LangGraph to decide tool usage  
- Responds with structured, explainable outputs  

Supports:

- News summaries  
- Weather  
- Stocks  
- Web search  
- Sports betting predictions  

---

# 2. Requirements

Install:

- Python 3.9+
- pip
- sqlite3
- Ollama

```bash
brew install ollama
ollama pull llama3
ollama serve
````

---

# 3. Installation

```bash
git clone git@github.com:rayme11/langgraph-ollama-agent.git
cd langgraph-ollama-agent

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

# 4. Environment Variables

Create `.env`:

```dotenv
# LLM
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# Weather
OPENWEATHER_API_KEY=

# Stocks
ALPHAVANTAGE_API_KEY=

# News
NEWS_API_KEY=

# Web Search
WEB_SEARCH_ENABLED=true
WEB_SEARCH_API_KEY=

# Database
DATABASE_URL=sqlite:///./app.db

# Sports Betting
ODDS_API_KEY=
SPORTSDATA_API_KEY=

SPORTSDATA_NBA_BASE_URL=https://api.sportsdata.io/v3/nba
SPORTSDATA_NFL_BASE_URL=https://api.sportsdata.io/v3/nfl
SPORTSDATA_MLB_BASE_URL=https://api.sportsdata.io/v3/mlb
SPORTSDATA_NHL_BASE_URL=https://api.sportsdata.io/v3/nhl
SPORTSDATA_CBB_BASE_URL=https://api.sportsdata.io/v3/cbb
SPORTSDATA_SOCCER_BASE_URL=https://api.sportsdata.io/v3/soccer
```

---

# 5. Project Structure

```
app/
  agent/
    graph.py
    tools.py
    sports_tools.py
    state.py
  memory/
    db.py
    schemas.py
  api/
    routes.py
  main.py

scripts/
  smoke_test_sports.py

streamlit_app.py
requirements.txt
.env
```

---

# 6. Tools Overview

| Tool            | Purpose        | API           |
| --------------- | -------------- | ------------- |
| get_weather     | Weather lookup | OpenWeather   |
| get_stock_quote | Stock prices   | AlphaVantage  |
| get_news        | News headlines | NewsAPI       |
| web_search      | Live search    | Tavily        |
| get_sports_odds | Betting odds   | The Odds API  |
| get_team_form   | Team stats     | Sportsdata.io |
| get_player_form | Player stats   | Sportsdata.io |

---

# 7. Sports Betting System

Supports:

* Moneyline
* Spreads
* Over/Under totals
* Player props
* Team performance trends
* Player performance trends
* Confidence classification:
  HIGH / MEDIUM / LOW / NOT RECOMMENDED

Uses:

1. The Odds API
2. Sportsdata.io
3. Implied probability
4. Historical form analysis
5. Matchup interpretation

---

# 8. LangGraph Agent Architecture

```
User → AgentNode → ToolNode → AgentNode → Final Answer
```

---

# 9. FastAPI API Usage

Run backend:

```bash
uvicorn app.main:app --reload
```

POST `/api/chat`:

```json
{
  "external_user_id": "user@example.com",
  "conversation_id": null,
  "user_text": "Is Lakers -3.5 a good bet tonight?"
}
```

---

# 10. Streamlit UI

```bash
streamlit run streamlit_app.py
```

Features:

* Chat history
* News, weather, stocks
* Sports betting queries

---

# 11. Sports Betting Examples

```
Is Lakers -3.5 a good bet tonight?
Is Cowboys +4.5 good this week?
Over 210.5 in Raptors vs Celtics?
Is LeBron over 26.5 points a good prop?
Is Inter Miami a good moneyline pick?
```

---

# 12. Testing & Smoke Tests

```bash
pytest -q
python -m scripts.smoke_test_sports
```

---

# 13. Troubleshooting

| Issue                | Fix                  |
| -------------------- | -------------------- |
| Missing API keys     | Add them to `.env`   |
| Ollama model missing | `ollama pull llama3` |
| No games found       | Increase `days_back` |
| API quota exceeded   | Upgrade tier         |

---

# 14. Disclaimer

This project is for **educational purposes only**.
No betting outcomes are guaranteed.
Bet responsibly.

```

---

