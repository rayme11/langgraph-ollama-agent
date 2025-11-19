from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as chat_router
from app.memory.db import init_db
from app.memory.schemas import HealthResponse


def create_app() -> FastAPI:
    app = FastAPI(
        title="LangGraph + Ollama Agent",
        version="0.1.0",
        description="A tutorial agent using LangGraph, LangChain tools, Ollama/OpenAI, and SQLite-backed memory.",
    )

    # CORS: allow everything in dev. Tighten for production.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # in prod, set specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def on_startup():
        # Ensure database tables exist
        init_db()

    @app.get("/health", response_model=HealthResponse, tags=["meta"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    # Mount chat API under /api
    app.include_router(chat_router, prefix="/api")

    return app


app = create_app()
