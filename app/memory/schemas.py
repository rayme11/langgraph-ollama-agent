from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """
    Request body for POST /api/chat.

    - external_user_id: your logical user identifier (email, UUID, etc.)
    - conversation_id: optional existing conversation; omit/null to start new.
    - user_text: the user's message.
    """
    external_user_id: str = Field(..., min_length=1, description="Logical user id (email, UUID, etc.)")
    conversation_id: Optional[int] = Field(
        None,
        description="Existing conversation id; omit/null to start a new one.",
    )
    user_text: str = Field(..., min_length=1, description="User message to the agent.")


class ChatResponse(BaseModel):
    """
    Response payload from POST /api/chat.

    - conversation_id: id of the conversation in the DB.
    - assistant: the assistant's latest reply text.
    """
    conversation_id: int
    assistant: str


class HealthResponse(BaseModel):
    """
    Response model for /health (useful if you want typed OpenAPI).
    """
    status: str = "ok"
