from fastapi import FastAPI

app = FastAPI(title="LangGraph + Ollama Agent")

@app.get("/health")
def health():
    return {"status": "ok"}
