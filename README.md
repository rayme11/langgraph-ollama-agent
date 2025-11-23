# 🧠 NewsGenie — AI-Powered News, Weather, Stocks & Web Search Assistant

An end-to-end agentic system built with **LangGraph**, **LangChain**, **Streamlit**, **FastAPI**, **SQLite**, and real-time APIs (NewsAPI, OpenWeatherMap, AlphaVantage, Tavily Search).  
Works with both **OpenAI** and **local LLMs via Ollama**.

---

## 🔧 Technology Stack

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![LangChain](https://img.shields.io/badge/Framework-LangChain-2C4F7C)
![LangGraph](https://img.shields.io/badge/Agents-LangGraph-8A2BE2)
![Ollama](https://img.shields.io/badge/Local_LLM-Ollama-000000?logo=ollama&logoColor=white)
![OpenAI](https://img.shields.io/badge/LLM-OpenAI-412991?logo=openai&logoColor=white)
![SQLite](https://img.shields.io/badge/DB-SQLite-07405E?logo=sqlite&logoColor=white)
![NewsAPI](https://img.shields.io/badge/News-NewsAPI-blue)
![OpenWeather](https://img.shields.io/badge/Weather-OpenWeatherMap-orange)
![AlphaVantage](https://img.shields.io/badge/Stocks-AlphaVantage-yellow)
![Tavily](https://img.shields.io/badge/Search-Tavily-purple)

---

## 🎥 Live Demo (10 seconds)

Here’s a quick demonstration of NewsGenie in action:

![NewsGenie Demo](docs/assets/demo_newsgenie.gif)

---

## 🖼 NewsGenie Architecture Diagram

Below is the high-level system architecture for the NewsGenie agentic workflow:

![NewsGenie Architecture](docs/assets/newsgenie_architecture.png)

---

# 📰 What NewsGenie Can Do

NewsGenie intelligently handles:
- 📰 **Real-time news** (technology, sports, business, science, etc.)
- 🌦️ **Weather lookups**
- 📈 **Stock quotes + risk classification**
- 🔎 **Live web search** (Tavily Search API)
- 💬 **General conversational queries**
- 🧠 **Full conversation memory** stored in SQLite

This project demonstrates:
- LLM tool use  
- Agentic workflows  
- Fallback logic  
- Multi-tool decision making  
- Persistent conversation memory  
- Complete web UI  
- API-layer abstraction  

---

# 📘 Table of Contents

1. Quickstart  
2. Requirements  
3. Environment Variables  
4. Project Structure  
5. Tools Overview  
6. LangGraph Agent Architecture  
7. FastAPI Backend  
8. Streamlit UI  
9. Example Queries  
10. Testing  
11. Troubleshooting  
12. Next Steps  

---

# 🚀 1. Quickstart (Fastest Way to Run)

Run NewsGenie locally in under 2 minutes.

---

### 1️⃣ Clone the repository

```bash
git clone git@github.com:rayme11/langgraph-ollama-agent.git
cd langgraph-ollama-agent
````

---

### 2️⃣ Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate     # macOS / Linux
# OR
.\.venv\Scripts\activate      # Windows
```

---

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Create your `.env` file

```bash
cp .env.example .env
```

Then fill in your API keys (NewsAPI, AlphaVantage, OpenWeather, Tavily, etc.)

Optional: enable OpenAI
Optional: enable local Ollama LLMs:

```bash
brew install ollama
ollama pull llama3
ollama serve
```

---

### 5️⃣ Initialize the SQLite database

```bash
python -c "from app.memory.db import init_db; init_db()"
```

---

### 6️⃣ Start the backend API (FastAPI)

```bash
uvicorn app.main:app --reload
```

Backend available at:

* [http://localhost:8000](http://localhost:8000)
* [http://localhost:8000/docs](http://localhost:8000/docs) (OpenAPI)

---

### 7️⃣ Start the Streamlit UI

Open a second terminal:

```bash
streamlit run streamlit_app.py
```

UI available via:

👉 [http://localhost:8501](http://localhost:8501)

---

🎉 **You are now running NewsGenie!**

Try:

* `Latest AI tech news?`
* `Weather in Austin,US?`
* `Is AAPL high risk today?`
* `Search SpaceX launch details`

---

# 2. Requirements

Install:

* Python 3.11+
* pip
* sqlite3

**Optional: Ollama for local LLMs**

```bash
brew install ollama
ollama pull llama3
ollama serve
```

**Optional: OpenAI**

---

# 3. Environment Variables

Create `.env`:

```dotenv
# --- LLM Providers ---
OPENAI_API_KEY=
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
OPENAI_MODEL=gpt-4o-mini

# --- Weather ---
OPENWEATHER_API_KEY=
OPENWEATHER_BASE_URL=https://api.openweathermap.org/data/2.5/weather

# --- Stocks ---
ALPHAVANTAGE_API_KEY=
ALPHAVANTAGE_BASE_URL=https://www.alphavantage.co

# --- News ---
NEWS_API_KEY=
NEWS_API_BASE_URL=https://newsapi.org/v2

# --- Web Search (Tavily) ---
WEB_SEARCH_ENABLED=true
WEB_SEARCH_API_KEY=

# --- Database ---
DATABASE_URL=sqlite:///./app.db
```

Copy example file:

```bash
cp .env.example .env
```

---

# 4. Project Structure

```
app/
  agent/
    graph.py
    tools.py
    state.py
  memory/
    db.py
    schemas.py
  api/
    routes.py
  main.py
scripts/
  smoke_test.py
tests/
  test_tools.py
  test_graph.py
streamlit_app.py
requirements.txt
README.md
.env
```

---

# 5. Tools Overview

| Tool              | Purpose                | API            |
| ----------------- | ---------------------- | -------------- |
| `get_weather`     | Real weather           | OpenWeatherMap |
| `get_stock_quote` | Stock prices           | AlphaVantage   |
| `stock_risk_hint` | Classify risk          | Internal logic |
| `get_news`        | Headlines & topic news | NewsAPI        |
| `web_search`      | General search         | Tavily Search  |

---

# 6. LangGraph Agent Architecture

```
User → AgentNode → (tool call?) → ToolNode → AgentNode → Response
```

Key components:

* AgentState
* System Prompt
* Tool Nodes
* Conditional edges
* SQLite persistence

Agent implementation:

```
app/agent/graph.py
```

---

# 7. FastAPI Backend

Start backend:

```bash
uvicorn app.main:app --reload
```

POST `/api/chat` example:

```json
{
  "external_user_id": "ray@example.com",
  "conversation_id": null,
  "user_text": "Latest AI tech news?"
}
```

---

# 8. Streamlit UI

Launch:

```bash
streamlit run streamlit_app.py
```

Features:

* Sidebar user identity
* Persistent memory
* Multi-category news
* Weather + stocks
* Tavily search integration

---

# 9. Example Queries

```
Weather in Tokyo?
Is AAPL high or low risk today?
What's happening in technology today?
Give me recent news about NVIDIA.
Search the web for SpaceX launch details.
Weather in Austin and latest AI news.
```

---

# 10. Testing

```bash
pytest -q
python scripts/smoke_test.py
```

---

# 11. Troubleshooting

### Missing API key

Add it to `.env`.

### Ollama model not found

```bash
ollama pull llama3
```

### News not loading

Check `NEWS_API_KEY`.

### Web search disabled

```
WEB_SEARCH_ENABLED=true
WEB_SEARCH_API_KEY=<your_key>
```

---

# 12. Next Steps

* Add RAG support
* Deploy to Streamlit Cloud / HuggingFace Spaces
* Dockerize backend + UI
* Add OAuth login
* Add analytics dashboards

---

```
