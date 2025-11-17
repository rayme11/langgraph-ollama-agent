
---

````md
# 🧠 LangGraph + Ollama Agent — Complete End-to-End Tutorial

This repository is a **full, practical guide** to building a LangGraph-powered intelligent agent that integrates:

- 🧩 **LangGraph** — agent reasoning & tool orchestration  
- ⚙️ **LangChain Tools** — API-driven Python functions  
- 🤖 **Ollama (Open Source LLMs)** — local inference (`llama3`, `mistral`)  
- ☁️ **OpenAI (Optional)** — cloud reasoning fallback (`gpt-4o-mini`)  
- 💾 **SQLite + SQLAlchemy** — persistent memory  
- ⚡ **FastAPI** — backend application  
- 🌦️ **Real APIs** — OpenWeatherMap & AlphaVantage  
- 🧪 **Smoke Test** — validates the full stack end-to-end  

---

# 📘 Table of Contents

1. [Step 1 — Project Setup & Secure Environment](#step-1--project-setup--secure-environment)  
 1.1 Why this step?  
 1.2 Prerequisites  
 1.3 Create and activate virtual environment  
 1.4 Install dependencies  
 1.5 Install and run Ollama  
 1.6 Secure environment setup  
 1.7 Create project structure  
 1.8 Create basic FastAPI skeleton  
2. [Step 2 — Database & Memory](#step-2--database--memory)  
3. [Step 3 — LangGraph Agent & Tools Integration](#step-3--langgraph-agent--tools-integration)  
4. Troubleshooting  
5. Next Steps  
6. Folder Layout  
7. Quickstart Summary  
8. License  

---

## 🧠 Step 1 — Project Setup & Secure Environment

### 1.1 Why this step?
We begin by establishing a clean, reproducible project foundation:
- Virtual environment isolation  
- Dependency control  
- Secure secret management  
- Verified local LLM runtime (Ollama)

---

### 1.2 Prerequisites

| Requirement | Description |
|--------------|-------------|
| **Python 3.11+** | Required for LangGraph, Pydantic v2 |
| **VS Code** | Recommended IDE |
| **Ollama** | Runs open-source LLMs locally |
| **API Keys** | OpenWeatherMap and AlphaVantage |

Sign up:  
🌦️ [https://openweathermap.org/api](https://openweathermap.org/api)  
📈 [https://www.alphavantage.co/support/#api-key](https://www.alphavantage.co/support/#api-key)

---

### 1.3 Create and activate virtual environment

```bash
git clone <YOUR_REPO_URL>
cd langgraph-ollama-agent

python3 -m venv .venv
source .venv/bin/activate        # macOS/Linux
.venv\Scripts\Activate.ps1       # Windows PowerShell
````

✅ You should see `(.venv)` prefix in your terminal prompt.

---

### 1.4 Install dependencies

Create a `requirements.txt` file:

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
```

Install dependencies:

```bash
pip install -r requirements.txt
```

✅ Installs FastAPI, LangGraph, SQLAlchemy, and other required packages.

---

### 1.5 Install and run Ollama

Install Ollama for your platform:

```bash
# macOS
brew install ollama
# Linux
curl -fsSL https://ollama.com/install.sh | sh
# Windows
winget install Ollama.Ollama
```

Start Ollama and pull models:

```bash
ollama serve
ollama pull llama3
ollama pull mistral
ollama list
```

✅ Ollama is now running locally at `http://localhost:11434`.

---

### 1.6 Secure environment setup

#### `.env.example` (safe to commit)

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

#### `.gitignore`

```gitignore
.env
*.env
app.db
__pycache__/
```

#### Create your local `.env`

```bash
cp .env.example .env
# Fill in your real keys locally
```

🚫 **Never commit `.env`**
If you accidentally did:

```bash
git rm --cached .env
git commit -m "Remove .env from tracking"
# Then rotate your keys
```

---

### 1.7 Create project structure

Organize the app for clarity and modularity:

```bash
mkdir -p app/agent app/memory app/api scripts tests
touch app/{__init__.py,main.py,config.py}
touch app/agent/{__init__.py,state.py,tools.py,graph.py}
touch app/memory/{__init__.py,db.py,schemas.py}
touch app/api/{__init__.py,routes.py}
```

✅ Clear separation:

* `agent/` — LangGraph + tools
* `memory/` — database
* `api/` — FastAPI endpoints

---

### 1.8 Create basic FastAPI skeleton

**File:** `app/main.py`

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

Visit: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
✅ Response: `{"status":"ok"}`

---

## 💾 Step 2 — Database & Memory

### 2.1 Why this step?

LangGraph’s state resets each run — we need persistent memory to store:

* Users
* Conversations
* Messages

---

### 2.2 Database schema

| Table           | Fields                                                        | Description           |
| --------------- | ------------------------------------------------------------- | --------------------- |
| `users`         | `id`, `external_id`, `created_at`                             | Unique logical users  |
| `conversations` | `id`, `user_id`, `title`, `created_at`                        | Chat threads per user |
| `messages`      | `id`, `conversation_id`, `role`, `content_json`, `created_at` | Full message history  |

---

### 2.3 Initialize the database

Run:

```bash
python -m app.memory.db
# ✅ Database initialized.
```

Start FastAPI (auto-creates if not present):

```bash
uvicorn app.main:app --reload
```

✅ You’ll see `app.db` in your project root.

---

### 2.4 Verify database

Use the **SQLite Viewer** extension in VS Code and open `app.db`.
Tables should be visible:

```
users
conversations
messages
```

✅ Database layer functional.

---

## 🤖 Step 3 — LangGraph Agent & Tools Integration

### 3.1 Message-based state

**File:** `app/agent/state.py`

```python
from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
```

💡 This keeps messages automatically appended to state.

---

### 3.2 Tools (API Integrations)

**File:** `app/agent/tools.py`

| Tool                      | API             | Description                      |
| ------------------------- | --------------- | -------------------------------- |
| `get_weather(city)`       | OpenWeatherMap  | Fetch temperature and conditions |
| `get_stock_quote(symbol)` | AlphaVantage    | Fetch stock quotes               |
| `stock_risk_hint()`       | Internal helper | Provides context for risk advice |

All tools are standard Python functions using `requests` and wrapped with `@tool` for LangGraph.

---

### 3.3 Model selection

**File:** `app/agent/graph.py`

| Condition                | Model Used                 |
| ------------------------ | -------------------------- |
| `OPENAI_API_KEY` present | `ChatOpenAI (gpt-4o-mini)` |
| No key                   | `ChatOllama (llama3)`      |

Override with `.env`:

```dotenv
OLLAMA_MODEL=mistral
OPENAI_MODEL=gpt-4o
```

---

### 3.4 LangGraph architecture

```
User → [Agent Node] --tools?--> [ToolNode executes] → [Agent Node] → END
```

* Agent decides when to use tools
* ToolNode executes API calls
* Agent summarizes tool outputs

---

### 3.5 `run_agent_turn()` helper

Handles a full reasoning loop:

1. Finds or creates user + conversation
2. Loads messages from DB
3. Executes the LangGraph run
4. Saves assistant + tool responses
5. Returns `{conversation_id, assistant_text}`

Example:

```python
from app.agent.graph import run_agent_turn
out = run_agent_turn("ray@example.com", None, "What's the weather in Austin?")
print(out)
```

✅ Assistant will return a contextual weather summary.

---

### 3.6 Smoke Test (End-to-End Validation)

Run:

```bash
python scripts/smoke_test.py
# or with arguments
python scripts/smoke_test.py --user ray@example.com --city "Austin,US" --symbol AAPL
```

It will:

1. Query current weather
2. Query stock info and assess risk
3. Persist conversation
4. Print LLM responses

**Expected output:**

```
--- Assistant (1) ---
The weather in Austin,US is 25°C and clear skies.

--- Assistant (1) ---
AAPL trades at $230, up 0.5%. Risk: Medium (not financial advice)
✅ Smoke test completed.
Conversation ID: 1
```

✅ Full system confirmed working.

---

## 🧩 Troubleshooting

| Issue                          | Resolution                                          |
| ------------------------------ | --------------------------------------------------- |
| `Missing OPENWEATHER_API_KEY`  | Add to `.env`                                       |
| `Missing ALPHAVANTAGE_API_KEY` | Add to `.env`                                       |
| Ollama connection errors       | Run `ollama serve`                                  |
| DB corrupted                   | Delete `app.db` and rerun `python -m app.memory.db` |

---

## 🚀 Next Steps

* Implement **numeric stock risk rubric** (Low/Medium/High thresholds)
* Add **error handling** for bad symbols or timeouts
* Write **unit tests** (mock requests)
* Expose **POST /chat** in FastAPI
* Experiment with **other Ollama models**

---

## 📁 Folder Layout

```
app/
  agent/
    state.py      # message-based state
    tools.py      # weather + stock tools
    graph.py      # LangGraph workflow
  memory/
    db.py         # ORM and helpers
    schemas.py
  api/
    routes.py     # (future endpoints)
  main.py         # FastAPI entrypoint
scripts/
  smoke_test.py   # validation script
requirements.txt
.env.example
.gitignore
README.md
```

---

## ⚡ Quickstart Summary

```bash
git clone <YOUR_REPO_URL>
cd langgraph-ollama-agent
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill in API keys
ollama serve
ollama pull llama3
python -m app.memory.db
python scripts/smoke_test.py
```

✅ Assistant replies with weather and stock messages → all modules working.

---

## 🧾 License

MIT License — for educational and experimental use.

---

## 👏 Credits

Created to teach:

* LangGraph agent architecture
* Persistent memory & tool orchestration
* Hybrid (local + cloud) reasoning models

Enjoy your **LangGraph + Ollama AI Agent! 🚀**

```

---

```
