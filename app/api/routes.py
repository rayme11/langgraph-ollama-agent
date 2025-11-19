# We’ll expose FastAPI routes to chat with the agent in Step 5.
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.agent.graph import run_agent_turn
from app.memory.schemas import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint.

    - Creates or reuses a conversation in the DB.
    - Invokes the LangGraph agent.
    - Returns the assistant reply + conversation id.

    Example body:
    {
      "external_user_id": "ray@example.com",
      "conversation_id": null,
      "user_text": "What's the weather in Austin?"
    }
    """
    user_text = payload.user_text.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="user_text cannot be empty or whitespace.")

    result = run_agent_turn(
        external_user_id=payload.external_user_id,
        conversation_id=payload.conversation_id,
        user_text=user_text,
    )

    # result is already shaped as {"conversation_id": int, "assistant": str}
    return ChatResponse(**result)
