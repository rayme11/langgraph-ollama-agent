
---

````md
# 🧠 LangGraph + Ollama Agent — Complete End-to-End Tutorial

This repository is a **complete, practical guide** to building a production-ready, tool-using agent powered by:

- 🧩 **LangGraph** for structured agent reasoning  
- ⚙️ **LangChain Tools** wrapping Python & HTTP APIs  
- 🤖 **Ollama (local open-source LLMs)** — Llama3, Mistral, Phi3, etc.  
- ☁️ **Optional OpenAI fallback** (`gpt-4o-mini`)  
- 💾 **SQLite + SQLAlchemy** for persistent memory  
- ⚡ **FastAPI** exposing `/api/chat`  
- 🌦️ **OpenWeatherMap** for real weather  
- 📈 **AlphaVantage** for real stock data  
- 🧪 **Pytest test suite**  
- 🔍 **Smoke test** to validate end-to-end behavior  

Everything is designed to be easy to extend and safe for local development.

---

# 📘 Table of Contents

1. Step 1 — Project Setup & Secure Environment  
2. Step 2 — Database & Memory  
3. Step 3 — LangGraph Agent & Tool Integration  
4. Step 4 — Risk Rubric, Error Handling & Tests  
5. Step 5 — FastAPI `/api/chat` Endpoint  
6. Troubleshooting  
7. Folder Layout  
8. Quickstart Summary  
9. License  

---

# 🧠 Step 1 — Project Setup & Secure Environment

## 1.1 Why this step?

We create a safe, reproducible environment:

- Python virtual environment  
- Dependency management  
- `.env` for API keys  
- Validate Ollama + Python installation  
- Proper project structure  

---

## 1.2 Prerequisites

| Requirement | Purpose |
|------------|---------|
| Python 3.11+ | LangGraph & Pydantic v2 support |
| VS Code | Recommended IDE |
| Ollama | Open-source local LLM runtime |
| API Keys | OpenWeatherMap + AlphaVantage |

Get API keys:

- 🌦️ https://openweathermap.org/api  
- 📈 https://www.alphavantage.co/support/#api-key  

---

## 1.3 Create and activate virtual environment

```bash
git clone <YOUR_REPO_URL>
cd langgraph-ollama-agent

python3 -m venv .venv
source .venv/bin/activate        # macOS/Linux
.venv\Scripts\Activate.ps1       # Windows PowerShell
````

---

## 1.4 Install dependencies

`requirements.txt`:

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

Install all:

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

Run and pull models:

```bash
ollama serve
ollama pull llama3
ollama pull mistral
ollama list
```

---

## 1.6 Secure environment setup

### `.env.example`

```dotenv
OPENAI_API_KEY=
OPENWEATHER_API_KEY=
ALPHAVANTAGE_API_KEY=
DATABASE_URL=sqlite:///./app.db
OLLAMA_BASE_URL=http://localhost:11434
# Optional overrides
# OLLAMA_MODEL=llama3
# OPENAI_MODEL=gpt-4o-mini
```

### `.gitignore`

```gitignore
.env
*.env
app.db
__pycache__/
```

### Create your actual `.env`

```bash
cp .env.example .env
```

🚫 If `.env` was committed accidentally:

```bash
git rm --cached .env
git commit -m "Remove .env from Git"
```

Rotate your keys.

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

## 1.8 Basic FastAPI skeleton

`app/main.py` (will be expanded in Step 5):

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

---

# 💾 Step 2 — Database & Memory

LangGraph’s state is ephemeral → we need persistent memory.

---

## 2.1 Schema

| Table           | Fields                                              |
| --------------- | --------------------------------------------------- |
| `users`         | id, external_id, created_at                         |
| `conversations` | id, user_id, title, created_at                      |
| `messages`      | id, conversation_id, role, content_json, created_at |

---

## 2.2 Initialize DB

```bash
python -m app.memory.db
```

Or start FastAPI (auto-creates tables):

```bash
uvicorn app.main:app --reload
```

---

## 2.3 Verify

Open `app.db` via the VS Code SQLite Viewer.

Should contain:

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

## 3.2 Tools — Weather, Stocks, Risk Rubric

Tools include:

* `get_weather`
* `get_stock_quote`
* `stock_risk_hint`

Using the `@tool` decorator, so the LLM can invoke them.

---

## 3.3 Model selection logic

If `OPENAI_API_KEY` is set → use OpenAI.
Else → use Ollama Llama3.

Override in `.env`:

```dotenv
OLLAMA_MODEL=mistral
OPENAI_MODEL=gpt-4o
```

---

## 3.4 LangGraph workflow

```
User → Agent Node → (Tool requested?) → ToolNode → Agent → END
```

---

## 3.5 `run_agent_turn()`

Handles:

1. Load or create user
2. Load or create conversation
3. Run the graph
4. Persist messages
5. Return assistant text

Example:

```python
from app.agent.graph import run_agent_turn
resp = run_agent_turn("ray@example.com", None, "Weather in Austin?")
print(resp)
```

---

## 3.6 Smoke Test

Run:

```bash
python scripts/smoke_test.py
```

Or:

```bash
python scripts/smoke_test.py --user ray@example.com --city "Austin,US" --symbol AAPL
```

Expected:

```
The weather is...
AAPL is trading at...
Risk: Medium
```

---

# 🧪 Step 4 — Risk Rubric, Error Handling & Tests

This step improves:

* stock risk rubric
* error handling for tools
* adds numeric percent change
* adds pytest testing

---

## 4.1 Updated `stock_risk_hint()`

Explicit rubric:

* Low risk: −1% → +1%
* Medium: −3% → −1% OR +1% → +3%
* High: < −3% OR > +3%

---

## 4.2 Improved `get_stock_quote`

Adds:

* structured errors
* `percent_change_float`
* safer conversions

---

## 4.3 Pytest installation

Already added to `requirements.txt`.

Run:

```bash
pytest -q
```

---

## 4.4 Tool tests

File: `tests/test_tools.py`

Covers:

* weather success
* stock success
* missing API keys

---

## 4.5 Graph tests using DummyLLM

File: `tests/test_graph.py`

This tests:

* conversation creation
* message persistence
* consistent agent reply

Without calling any real LLM.

---

# ⚡ Step 5 — FastAPI `/api/chat` Endpoint

We now expose the agent as a real API.

---

## 5.1 Create Pydantic request/response models

`app/memory/schemas.py`:

```python
from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    external_user_id: str = Field(..., min_length=1)
    conversation_id: Optional[int] = None
    user_text: str = Field(..., min_length=1)

class ChatResponse(BaseModel):
    conversation_id: int
    assistant: str

class HealthResponse(BaseModel):
    status: str = "ok"
```

---

## 5.2 Create the `/api/chat` route

`app/api/routes.py`:

```python
from fastapi import APIRouter, HTTPException
from app.agent.graph import run_agent_turn
from app.memory.schemas import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    if not payload.user_text.strip():
        raise HTTPException(status_code=400, detail="user_text cannot be empty.")

    result = run_agent_turn(
        external_user_id=payload.external_user_id,
        conversation_id=payload.conversation_id,
        user_text=payload.user_text.strip(),
    )
    return ChatResponse(**result)
```

---

## 5.3 Update `app/main.py` to include the router

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as chat_router
from app.memory.db import init_db
from app.memory.schemas import HealthResponse

def create_app() -> FastAPI:
    app = FastAPI(
        title="LangGraph + Ollama Agent",
        version="0.1.0",
        description="Agent with LangGraph + Ollama + FastAPI.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def startup_event():
        init_db()

    @app.get("/health", response_model=HealthResponse)
    def health():
        return HealthResponse()

    app.include_router(chat_router, prefix="/api")
    return app

app = create_app()
```

---

## 5.4 Usage examples

### Start server

```bash
uvicorn app.main:app --reload
```

### Start a new conversation

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
        "external_user_id": "ray@example.com",
        "conversation_id": null,
        "user_text": "Weather in Austin,US?"
      }'
```

### Continue conversation

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
        "external_user_id": "ray@example.com",
        "conversation_id": 1,
        "user_text": "Check AAPL risk today"
      }'
```

---

# 🧩 Troubleshooting

| Issue                  | Fix                      |
| ---------------------- | ------------------------ |
| Missing API keys       | Fill `.env`              |
| Ollama not running     | `ollama serve`           |
| DB corrupted           | Remove `app.db` → reinit |
| Tools returning errors | Check API quotas         |

---

# 📁 Folder Layout

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
# Add API keys for weather + stocks

ollama serve
ollama pull llama3

python -m app.memory.db

python scripts/smoke_test.py

uvicorn app.main:app --reload

pytest -q
```

---

# 🧾 License

MIT — educational and experimental use.

---

# 👏 Credits

Built to teach:

* Tool-calling agents
* Persistent conversational memory
* Hybrid LLM architecture (Ollama + OpenAI)
* FastAPI integration
* Real API-driven agent workflows

Enjoy your **LangGraph + Ollama Agent! 🚀**

```

---

```
