
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

## 🎥 Live Demo (Optional)

![NewsGenie Demo](docs/assets/demo_newsgenie.gif)

---

## 🖼 Architecture Diagram (Optional)

![NewsGenie Architecture](docs/assets/newsgenie_architecture.png)

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

- Python 3.9+
- pip
- sqlite3
- **Ollama (local LLM)**

```bash
brew install ollama
ollama pull llama3
ollama serve
````

Optional:

* OpenAI API key for cloud inference

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
ODDS_API_KEY=                    # The Odds API
SPORTSDATA_API_KEY=              # Sportsdata.io

SPORTSDATA_NBA_BASE_URL=https://api.sportsdata.io/v3/nba
SPORTSDATA_NFL_BASE_URL=https://api.sportsdata.io/v3/nfl
SPORTSDATA_MLB_BASE_URL=https://api.sportsdata.io/v3/mlb
SPORTSDATA_NHL_BASE_URL=https://api.sportsdata.io/v3/nhl
SPORTSDATA_CBB_BASE_URL=https://api.sportsdata.io/v3/cbb
SPORTSDATA_SOCCER_BASE_URL=https://api.sportsdata.io/v3/soccer
```

---

# 5. Project Structure

```text
app/
  agent/
    graph.py              # LangGraph workflow
    tools.py              # All tools registry
    sports_tools.py       # Odds + team + player stats
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

NewsGenie supports:

* ✅ Moneyline bets (+150 / -180)
* ✅ Point spreads (Team -3.5, +4.5)
* ✅ Totals (Over / Under)
* ✅ Player props (Over 26.5 points)
* ✅ Team & player historical performance
* ✅ LOW / MEDIUM / HIGH confidence classification

### How recommendations are calculated:

1. Fetch live odds with **The Odds API**
2. Fetch team form (last N days) with **Sportsdata.io**
3. Optional: Fetch player form for props
4. Compute implied probability
5. Analyze recent scoring margins, trends, and matchups
6. Classify confidence level:

   * HIGH
   * MEDIUM
   * LOW
   * NOT RECOMMENDED

⚠️ Always includes a **risk disclaimer**

---

# 8. LangGraph Agent Architecture

```text
User → AgentNode → ToolNode → AgentNode → Final Answer
```

The system automatically:

* Decides which tool to call
* Handles multiple tool calls per prompt
* Applies the betting rubric via system prompt

---

# 9. FastAPI Backend

Start backend:

```bash
uvicorn app.main:app --reload
```

### POST `/api/chat`

Body:

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

Start UI:

```bash
streamlit run streamlit_app.py
```

Supports:

* Chat interface
* Persistent history
* Betting questions
* News, weather, stocks

---

# 11. Sports Betting Example Prompts

```text
Is Lakers -3.5 a good bet tonight?

Is Cowboys +4.5 good this week in the NFL?

Is LeBron over 26.5 points a good prop bet?

Over 210.5 in Raptors vs Celtics?

Based on the last 5 days, is Inter Miami a good moneyline bet today?
```

---

# 12. Testing & Smoke Tests

### Run unit tests:

```bash
pytest -q
```

### Run sports betting smoke test:

```bash
python -m scripts.smoke_test_sports
```

This validates:

* Odds retrieval
* Team & player stats
* End-to-end LangGraph execution

---

# 13. Troubleshooting

| Issue                      | Fix                        |
| -------------------------- | -------------------------- |
| Missing ODDS_API_KEY       | Add it to `.env`           |
| Missing SPORTSDATA_API_KEY | Add it to `.env`           |
| Ollama model not found     | `ollama pull llama3`       |
| No games found             | Try increasing `days_back` |
| API quota exceeded         | Upgrade API tier           |

---

# 14. ⚠️ Legal & Financial Disclaimer

This project is **for educational and informational purposes only**.

* **No betting advice is guaranteed**
* **No financial outcome is promised**
* Sports betting contains significant risk
* Always bet responsibly
* The developers are not responsible for financial losses

---

✅ **NewsGenie now supports live sports betting intelligence with full explainability, real-time odds, and statistical reasoning.**

````

---

