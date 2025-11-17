# We’ll define Pydantic models & ORM models in Step 2.
from __future__ import annotations
import datetime as dt
from typing import Optional
from pydantic import BaseModel

class MessageOut(BaseModel):
    id: int
    role: str
    content: dict
    created_at: dt.datetime

class ConversationOut(BaseModel):
    id: int
    title: Optional[str]
    created_at: dt.datetime
    messages: list[MessageOut]
