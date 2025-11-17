# We’ll set up SQLAlchemy (SQLite) & session management in Step 2.
from __future__ import annotations
import json
import datetime as dt
from contextlib import contextmanager
from typing import Generator, Optional, Literal
from sqlalchemy import create_engine, ForeignKey, String, DateTime, Text
from sqlalchemy import select, func
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)
from pydantic import BaseModel
from app.config import get_settings

settings = get_settings()

# --- Engine & Session ---
# SQLite for local dev. For production, swap DATABASE_URL to Postgres (e.g., postgresql+psycopg://...)
engine = create_engine(settings.database_url, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)


class Base(DeclarativeBase):
    pass


# --- ORM Models ---
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # You can map this to your auth’s subject or email; keep it generic for now.
    external_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc))

    conversations: Mapped[list["Conversation"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[Optional[str]] = mapped_column(String(200), default=None)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc))

    user: Mapped["User"] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    # 'user' | 'assistant' | 'tool'
    role: Mapped[str] = mapped_column(String(20))
    # Store LLM messages as JSON (content, tool_calls, etc.)
    content_json: Mapped[str] = mapped_column(Text)  # JSON string
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc))

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")

    # Helpers
    @property
    def content(self) -> dict:
        return json.loads(self.content_json)

    @staticmethod
    def to_json(content: dict | list | str) -> str:
        # Normalize to dict form; LangChain messages will later fit here natively.
        if isinstance(content, (dict, list)):
            return json.dumps(content, ensure_ascii=False)
        return json.dumps({"text": str(content)}, ensure_ascii=False)


# --- Session helper ---
@contextmanager
def get_session() -> Generator:
    """Context manager to yield a DB session and ensure proper cleanup."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# --- CRUD / Repository helpers (used by routes & agent logic later) ---

def upsert_user(session, external_id: str) -> User:
    user = session.scalar(select(User).where(User.external_id == external_id))
    if user:
        return user
    user = User(external_id=external_id)
    session.add(user)
    session.flush()
    return user


def create_conversation(session, user: User, title: Optional[str] = None) -> Conversation:
    conv = Conversation(user_id=user.id, title=title)
    session.add(conv)
    session.flush()
    return conv


def append_message(
    session,
    conversation: Conversation,
    role: Literal["user", "assistant", "tool"],
    content: dict | list | str,
) -> Message:
    msg = Message(conversation_id=conversation.id, role=role, content_json=Message.to_json(content))
    session.add(msg)
    session.flush()
    return msg


def get_conversation_with_messages(session, conversation_id: int) -> Optional[Conversation]:
    return session.get(Conversation, conversation_id)


def list_conversations_for_user(session, user: User, limit: int = 20) -> list[Conversation]:
    stmt = (
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.created_at.desc())
        .limit(limit)
    )
    return list(session.scalars(stmt))


# --- Pydantic response schemas (handy for API responses) ---
class MessageOut(BaseModel):
    id: int
    role: str
    content: dict
    created_at: dt.datetime

    @classmethod
    def from_orm_msg(cls, m: Message) -> "MessageOut":
        return cls(id=m.id, role=m.role, content=m.content, created_at=m.created_at)


class ConversationOut(BaseModel):
    id: int
    title: Optional[str]
    created_at: dt.datetime
    messages: list[MessageOut]


# --- DB bootstrap ---
def init_db() -> None:
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    # Allow quick CLI init: `python -m app.memory.db`
    init_db()
    print("✅ Database initialized.")
