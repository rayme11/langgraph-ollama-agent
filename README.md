
````markdown
# 🧠 NewsGenie — AI-Powered News, Weather, Stocks & Sports Betting Assistant

NewsGenie is an end-to-end **agentic AI system** built with **LangGraph**, **LangChain**, **FastAPI**, **Streamlit**, **SQLite**, and real-time APIs for:

- 📰 News  
- 🌦️ Weather  
- 📈 Stocks  
- 🔎 Web Search  
- 🏀🏈⚽ **Sports Betting Analysis & Recommendations**  

It works with both **OpenAI** and **local LLMs via Ollama** and provides:

- Tool-using AI agents  
- Live data fetching  
- Sports betting recommendations (LOW / MEDIUM / HIGH / NOT RECOMMENDED)  
- Persistent conversation memory  

---

## 🔧 Technology Stack

- Python 3.9+
- LangChain
- LangGraph
- FastAPI
- Streamlit
- SQLite
- Ollama (local LLM)
- OpenAI (optional)
- OpenWeatherMap
- AlphaVantage (stocks)
- NewsAPI
- Tavily Search API
- The Odds API (sports betting)
- Sportsdata.io (team & player statistics)

---

## 🎥 Live Demo (Optional)

![NewsGenie Demo](https://raw.githubusercontent.com/rayme11/langgraph-ollama-agent/main/docs/assets/demo_newsgenie.gif)

---

## 🖼 Architecture Diagram (Optional)

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

- Detects what the user is asking
- Calls the correct API automatically
- Reasons over live data
- Produces structured explanations

It supports:

- News summaries  
- Weather lookups  
- Stock quotes and risk classification  
- Web search  
- Sports betting odds & recommendations  

---

# 2. Requirements

Install:

```bash
brew install ollama
ollama pull llama3
ollama serve
````

Optional:

* OpenAI API Key

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
# ---- LLM ----
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# ---- Weather ----
OPENWEATHER_API_KEY=

# ---- Stocks ----
ALPHAVANTAGE_API_KEY=

# ---- News ----
NEWS_API_KEY=

# ---- Web Search ----
WEB_SEARCH_ENABLED=true
WEB_SEARCH_API_KEY=

# ---- Database ----
DATABASE_URL=sqlite:///./app.db

# ---- Sports Betting ----
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
README.md
.env
```

---

# 6. Tools Overview

| Tool            | Purpose                   | API           |
| --------------- | ------------------------- | ------------- |
| get_weather     | Weather lookup            | OpenWeather   |
| get_stock_quote | Stock prices              | AlphaVantage  |
| get_news        | Live news                 | NewsAPI       |
| web_search      | General search            | Tavily        |
| get_sports_odds | Live betting odds         | The Odds API  |
| get_team_form   | Team recent performance   | Sportsdata.io |
| get_player_form | Player recent performance | Sportsdata.io |

---

# 7. 🏀 Sports Betting System

Supports:

* Moneyline (+150 / -180)
* Point spreads (Team -3.5, +4.5)
* Totals (Over / Under)
* Player props
* Team & player stats (last N days)
* LOW / MEDIUM / HIGH confidence classification

Recommendations use:

1. Live odds
2. Team form
3. Player form
4. Implied probabilities
5. Trend analysis

Always includes a **risk disclaimer**.

---

# 8. LangGraph Agent Architecture

```
User → AgentNode → ToolNode → AgentNode → Final Answer
```

Agent automatically:

* Selects the correct tool
* Handles multi-step tool usage
* Applies betting rubric

---

# 9. FastAPI Backend

Start:

```bash
uvicorn app.main:app --reload
```

### POST `/api/chat`

Request:

```json
{
  "external_user_id": "user@example.com",
  "conversation_id": null,
  "user_text": "Is Lakers -3.5 a good bet tonight?"
}
```

Response:

```json
{
  "conversation_id": 12,
  "assistant": "Based on odds and recent form..."
}
```

---

# 10. Streamlit UI

Start:

```bash
streamlit run streamlit_app.py
```

Features:

* Full chat interface
* Persistent memory
* Supports betting, weather, stocks, news

---

# 11. Sports Betting Example Prompts

```
Is Lakers -3.5 a good bet tonight?
Is Cowboys +4.5 good this week?
Is LeBron over 26.5 points a good prop?
Over 210.5 in Raptors vs Celtics?
Based on last 5 days, is Inter Miami a good moneyline bet?
```

---

# 12. Testing & Smoke Tests

Run full tests:

```bash
pytest -q
```

Run sports smoke test:

```bash
python -m scripts.smoke_test_sports
```

---

# 13. Troubleshooting

| Issue                      | Fix                  |
| -------------------------- | -------------------- |
| Missing ODDS_API_KEY       | Add to `.env`        |
| Missing SPORTSDATA_API_KEY | Add to `.env`        |
| Ollama model missing       | `ollama pull llama3` |
| No games found             | Increase `days_back` |
| API quota exceeded         | Upgrade plan         |

---

# 14. ⚠️ Disclaimer

This project is for **educational purposes only**.
No betting advice is guaranteed.
Always gamble responsibly.

---

✅ NewsGenie now supports **live sports betting intelligence**, **news**, **weather**, **stocks**, **search**, and **full agentic workflows**.

```

