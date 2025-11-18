from __future__ import annotations

import pytest
from langchain_core.messages import AIMessage

from app.agent import graph as graph_module
from app.memory.db import init_db


class DummyLLM:
    """
    Simple fake LLM for testing the graph:
      - bind_tools(...) returns self
      - invoke(...) returns a fixed AIMessage
    """
    def bind_tools(self, tools):
        # In real life we might inspect tools; for this test we ignore them.
        return self

    def invoke(self, messages, config=None):
        # Always respond with a simple text
        return AIMessage(content="This is a dummy response.")


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    # Ensure DB tables exist for the test session
    init_db()
    yield


@pytest.fixture(autouse=True)
def patch_build_llm(monkeypatch):
    # Patch build_llm so graph uses DummyLLM instead of real Ollama/OpenAI
    monkeypatch.setattr(graph_module, "build_llm", lambda: DummyLLM())
    yield


def test_run_agent_turn_creates_conversation_and_messages():
    # Act
    result = graph_module.run_agent_turn(
        external_user_id="test_user@example.com",
        conversation_id=None,
        user_text="Hello, agent!",
    )

    # Assert
    assert "conversation_id" in result
    assert result["assistant"] == "This is a dummy response."
    assert isinstance(result["conversation_id"], int)

    # Second turn: ensure we can continue the same conversation
    conv_id = result["conversation_id"]
    result2 = graph_module.run_agent_turn(
        external_user_id="test_user@example.com",
        conversation_id=conv_id,
        user_text="Second message.",
    )
    assert result2["conversation_id"] == conv_id
    assert result2["assistant"] == "This is a dummy response."
