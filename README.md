# LangGraph + Ollama Agent

A step-by-step tutorial project that builds a LangGraph-powered agent with:
- Tools as normal Python functions (via `requests`)
- Wrapped as LangChain tools
- Message-based state & memory (SQLite)
- Reasoning engine: OpenAI `ChatOpenAI` (optional) and OSS via Ollama (`llama3`, `mistral`)
- Useful tools: stock advisory & weather lookup via real APIs
- FastAPI backend

## Quickstart
1. Install Python 3.11+ and VS Code.
2. `python -m venv .venv && source .venv/bin/activate` (Windows: `.venv\\Scripts\\Activate.ps1`)
3. `pip install -r requirements.txt`
4. Install **Ollama** and pull at least one model:
   - `ollama pull llama3`
5. Copy `.env.example` to `.env` and add your API keys.
6. Run the server (later): `uvicorn app.main:app --reload` (we’ll wire routes in later steps)
