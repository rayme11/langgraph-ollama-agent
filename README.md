
````md
# 🧠 LangGraph + Ollama Agent — Complete End-to-End Tutorial

This repository is a **complete, practical guide** to building an intelligent agent using:

- 🧩 **LangGraph** for tool-calling agent reasoning  
- ⚙️ **LangChain Tools** wrapping Python + HTTP APIs  
- 🤖 **Ollama (local LLMs)** like `llama3`, `mistral`  
- ☁️ **Optional OpenAI fallback** (`gpt-4o-mini`)  
- 💾 **SQLite + SQLAlchemy** for persistent memory  
- ⚡ **FastAPI** backend  
- 🌦️ **Weather API** (OpenWeatherMap)  
- 📈 **Stock API** (AlphaVantage)  
- 🧪 **Pytest-based test suite**  
- 🔍 **Smoke test** to validate the full stack  

---

# 📘 Table of Contents

1. Step 1 — Project Setup & Secure Environment  
2. Step 2 — Database & Memory  
3. Step 3 — LangGraph Agent & Tool Integration  
4. Step 4 — Risk Rubric, Error Handling & Tests  
5. Troubleshooting  
6. Folder Layout  
7. Quickstart Summary  
8. License  

---

# 🧠 Step 1 — Project Setup & Secure Environment

## 1.1 Why this step?

We establish a clean foundation:
- virtual environment  
- dependency management  
- secure secret handling  
- validating Ollama and Python runtime  

---

## 1.2 Prerequisites

| Requirement | Purpose |
|------------|---------|
| Python 3.11+ | Required for LangGraph & Pydantic v2 |
| VS Code | Recommended environment |
| Ollama | Local LLM runtime |
| API keys | OpenWeatherMap + AlphaVantage |

Sign-up pages:  
🌦️ https://openweathermap.org/api  
📈 https://www.alphavantage.co/support/#api-key  

---

## 1.3 Create and activate virtual environment

```bash
git clone <YOUR_REPO_URL>
cd langgraph-ollama-agent

python3 -m venv .venv
source .venv/bin/activate        # macOS/Linux
.venv\Scripts\Activate.ps1       # Windows
````

You should see `(.venv)` in your shell.

---

## 1.4 Install dependencies

Create `requirements.txt`

```txt
fastapi
uvicorn[standard]
python-dotenv
requests
pydantic>=2
SQLAlchemy>=2
langchain>=0.3
langchain-openai>=0.2
langchain-community>=0.3
langgraph>=0.2
tenacity
httpx
ruff
pytest
pytest-mock
```

Install:

```bash
pip install -r requirements.txt
```

---

## 1.5 Install and run Ollama

```bash
# macOS
brew install ollama
# Linux
curl -fsSL https://ollama.com/install.sh | sh
# Windows
winget install Ollama.Ollama
```

Start Ollama & pull models:

```bash
ollama serve
ollama pull llama3
ollama pull mistral
ollama list
```

---

## 1.6 Secure environment setup

### `.env.example` (safe to commit)

```dotenv
OPENAI_API_KEY=
OPENWEATHER_API_KEY=
ALPHAVANTAGE_API_KEY=
DATABASE_URL=sqlite:///./app.db
OLLAMA_BASE_URL=http://localhost:11434
# Optional overrides
# OPENAI_MODEL=gpt-4o-mini
# OLLAMA_MODEL=llama3
```

### `.gitignore`

```gitignore
.env
*.env
app.db
__pycache__/
```

### Create your local `.env`

```bash
cp .env.example .env
```

🚫 If `.env` was committed:

```bash
git rm --cached .env
git commit -m "Remove .env from tracking"
```

Rotate your API keys.

---

## 1.7 Create project structure

```bash
mkdir -p app/agent app/memory app/api scripts tests
touch app/{__init__.py,main.py,config.py}
touch app/agent/{__init__.py,state.py,tools.py,graph.py}
touch app/memory/{__init__.py,db.py,schemas.py}
touch app/api/{__init__.py,routes.py}
```

---

## 1.8 FastAPI skeleton

`app/main.py`:

```python
from fastapi import FastAPI

app = FastAPI(title="LangGraph + Ollama Agent")

@app.get("/health")
def health():
    return {"status": "ok"}
```

Run:

```bash
uvicorn app.main:app --reload
```

Open: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

# 💾 Step 2 — Database & Memory

LangGraph state resets each run → we need **persistent memory**.

---

## 2.1 Schema overview

| Table         | Fields                                              |
| ------------- | --------------------------------------------------- |
| users         | id, external_id, created_at                         |
| conversations | id, user_id, title, created_at                      |
| messages      | id, conversation_id, role, content_json, created_at |

---

## 2.2 Initialize database

```bash
python -m app.memory.db
```

Or run FastAPI (it auto-creates tables):

```bash
uvicorn app.main:app --reload
```

You should see `app.db`.

---

## 2.3 Verify database

Use VS Code SQLite Viewer.

Expected tables:

* users
* conversations
* messages

---

# 🤖 Step 3 — LangGraph Agent & Tool Integration

## 3.1 Message-based state

`app/agent/state.py`:

```python
from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
```

---

## 3.2 Tools (API Integrations)

`get_weather`
`get_stock_quote`
`stock_risk_hint`

Each wrapped with `@tool` so LangGraph can call them automatically.

---

## 3.3 Model selection

In `graph.py`:

| Condition           | Model                       |
| ------------------- | --------------------------- |
| Have OPENAI_API_KEY | ChatOpenAI                  |
| Else                | ChatOllama (llama3 default) |

Override via `.env`:

```dotenv
OLLAMA_MODEL=mistral
OPENAI_MODEL=gpt-4o
```

---

## 3.4 LangGraph architecture

```
User → Agent Node → [tool?] → ToolNode → Agent → END
```

Tools execute **only** when the LLM decides they are needed.

---

## 3.5 `run_agent_turn()` helper

Handles:

1. Create/load user
2. Load conversation history
3. Run LangGraph
4. Persist messages
5. Return assistant text

Usage:

```python
from app.agent.graph import run_agent_turn
resp = run_agent_turn("ray@example.com", None, "Weather in Austin?")
print(resp)
```

---

## 3.6 Smoke Test (End-to-End)

Run:

```bash
python scripts/smoke_test.py
```

Or:

```bash
python scripts/smoke_test.py --user ray@example.com --city "Austin,US" --symbol AAPL
```

Expected output:

```
--- Assistant (1) ---
The weather in Austin,...

--- Assistant (1) ---
AAPL trades at...
Risk: Medium
```

---

# 🧪 Step 4 — Risk Rubric, Error Handling & Tests

This step introduces:

* Stronger **stock risk rubric**
* Improved **stock tool error handling**
* `percent_change_float` for math
* **Pytest test suite**
* A **dummy LLM** for graph tests (offline)

---

## 4.1 Updated `stock_risk_hint()`

```python
def stock_risk_hint() -> str:
    return (
        "Use this rubric for risk levels:\n"
        "- Low risk: price change between -1% and +1%\n"
        "- Medium risk: -3% to -1% OR +1% to +3%\n"
        "- High risk: < -3% or > +3%\n\n"
        "Explain reasoning and note this is not financial advice."
    )
```

---

## 4.2 Improved `get_stock_quote`

Includes:

* consistent error structures
* numeric `percent_change_float`

---

## 4.3 Install pytest

Add to `requirements.txt` (already included above):

```txt
pytest
pytest-mock
```

Install:

```bash
pip install -r requirements.txt
```

---

## 4.4 Unit test the tools

Create:

`tests/test_tools.py`

(Tests weather + stock tools using mocked HTTP responses.)

Run:

```bash
pytest tests/test_tools.py -q
```

---

## 4.5 Test the LangGraph agent with a DummyLLM

Create:

`tests/test_graph.py`

Run:

```bash
pytest tests/test_graph.py -q
```

All tests run offline — no LLM, no network.

---

# 🧩 Troubleshooting

| Issue              | Fix                                 |
| ------------------ | ----------------------------------- |
| Missing API keys   | Add to `.env`                       |
| Ollama not running | `ollama serve`                      |
| DB locked          | delete `app.db` → reinit            |
| Bad symbols        | stock tool returns structured error |

---

# 📁 Folder Layout

```
app/
  agent/
    tools.py
    graph.py
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
requirements.txt
.env.example
README.md
```

---

# ⚡ Quickstart Summary

```bash
git clone <YOUR_REPO_URL>
cd langgraph-ollama-agent
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
ollama serve
ollama pull llama3
python -m app.memory.db
python scripts/smoke_test.py
pytest -q
```

---

# 🧾 License

MIT — educational and experimental use only.

---

# 👏 Credits

Built to teach **tool-calling agent design**, **persistent memory**, and **local LLM development using LangGraph + Ollama**.

```

---

```
