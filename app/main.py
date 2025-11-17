from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.memory.db import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown (nothing to clean up now)

app = FastAPI(title="LangGraph + Ollama Agent", lifespan=lifespan)

@app.get("/health")
def health():
    return {"status": "ok"}
