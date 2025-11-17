from __future__ import annotations

import os
from typing import Optional

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    ToolMessage,
    SystemMessage,
)
from langchain_core.runnables import RunnableConfig

# Models
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama

# Our state & tools
from app.agent.state import AgentState
from app.agent.tools import TOOLS, stock_risk_hint
from app.config import get_settings

# DB helpers
from app.memory.db import (
    get_session,
    upsert_user,
    create_conversation,
    get_conversation_with_messages,
    append_message,
)

settings = get_settings()


# ---------------------------------------------------------------------
# Model factory
# ---------------------------------------------------------------------
def build_llm():
    """
    Prefer OpenAI if key exists; otherwise use local Ollama.

    You can set:
      - OPENAI_MODEL (default: gpt-4o-mini)
      - OLLAMA_MODEL (default: llama3)
    """
    if settings.openai_api_key:
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0.2
        )
    return ChatOllama(
        base_url=settings.ollama_base_url,
        model=os.getenv("OLLAMA_MODEL", "llama3"),
        temperature=0.2,
    )


# ---------------------------------------------------------------------
# Agent (LLM) node
# ---------------------------------------------------------------------
def call_model(state: AgentState, config: Optional[RunnableConfig] = None):
    """
    Core reasoning step. The LLM may return:
      - a normal text response, OR
      - structured tool calls (handled by ToolNode).
    """
    llm = build_llm().bind_tools(TOOLS)

    system = SystemMessage(
        content=(
            "You are a helpful assistant that can call tools when needed. "
            "Use tools for factual lookups (weather, stock quotes). "
            "If you can answer without tools, be brief and clear.\n\n"
            "For stock advisory tasks, use this hint:\n"
            f"{stock_risk_hint()}\n"
            "Always cite the fields you used from tool outputs (price, percent change, etc.). "
            "Be transparent that this is not financial advice."
        )
    )
    messages = [system] + state["messages"]
    response = llm.invoke(messages, config=config)
    return {"messages": [response]}


# ---------------------------------------------------------------------
# Tool execution node
# ---------------------------------------------------------------------
tool_node = ToolNode(TOOLS)


# ---------------------------------------------------------------------
# Graph builder & compiled graph
# ---------------------------------------------------------------------
def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("agent", call_model)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("agent")

    # If LLM emitted tool calls → go to ToolNode; else → END
    graph.add_conditional_edges(
        "agent",
        tools_condition,
        {"tools": "tools", END: END},
    )

    # After tools run, return control to the agent to summarize/answer
    graph.add_edge("tools", "agent")

    return graph.compile()


GRAPH = build_graph()


# ---------------------------------------------------------------------
# High-level: run one chat turn and persist memory
# ---------------------------------------------------------------------
def run_agent_turn(
    external_user_id: str,
    conversation_id: int | None,
    user_text: str,
) -> dict:
    """
    - Ensures user + conversation exist
    - Appends the new user message
    - Reconstructs message history into LangChain message objects
    - Invokes the LangGraph
    - Persists new assistant/tool messages
    - Returns conversation_id + latest assistant text
    """
    with get_session() as s:
        user = upsert_user(s, external_id=external_user_id)

        if conversation_id is None:
            conv = create_conversation(s, user, title="New chat")
        else:
            conv = get_conversation_with_messages(s, conversation_id)
            if not conv:
                conv = create_conversation(s, user, title="New chat")

        # 1) Append incoming user message
        append_message(s, conv, role="user", content={"text": user_text})

        # 2) Convert DB messages → LangChain messages
        # Note: Only reconstruct user/assistant messages that came from actual turns.
        # Tool messages are handled during the current GRAPH.invoke() call.
        lc_messages = []
        for m in conv.messages:
            role = m.role
            payload = m.content  # dict we stored
            text = payload.get("text")

            if role == "user":
                lc_messages.append(HumanMessage(content=text))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=text))
            # Skip tool messages from history - they'll be created fresh by ToolNode
            # elif role == "tool":
            #     name = payload.get("tool_name", "tool")
            #     tool_call_id = payload.get("tool_call_id", f"call_{m.id}")
            #     lc_messages.append(ToolMessage(content=str(text), name=name, tool_call_id=tool_call_id))
            else:
                lc_messages.append(AIMessage(content=str(payload)))

        state: AgentState = {"messages": lc_messages}

        # 3) Run the graph
        result = GRAPH.invoke(state)

        # 4) Persist only the messages produced in this turn (after our prior history)
        new_messages = result["messages"][len(lc_messages) :]

        last_assistant_text = None
        for msg in new_messages:
            if isinstance(msg, AIMessage):
                last_assistant_text = (
                    msg.content if isinstance(msg.content, str) else str(msg.content)
                )
                append_message(
                    s, conv, role="assistant", content={"text": last_assistant_text}
                )
            elif isinstance(msg, ToolMessage):
                append_message(
                    s,
                    conv,
                    role="tool",
                    content={"tool_name": msg.name or "tool", "text": str(msg.content)},
                )

        return {"conversation_id": conv.id, "assistant": last_assistant_text or ""}
