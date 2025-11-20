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
# NewsGenie System Prompt
# ---------------------------------------------------------------------
AGENT_SYSTEM_PROMPT = """
You are NewsGenie — an AI-powered information and news assistant.

Your capabilities:
1. General conversation and explanation.
2. Real-time weather lookups using the get_weather tool.
3. Real-time stock quotes using the get_stock_quote tool.
4. Stock risk assessment using the risk rubric below.
5. Real-time news fetching using the get_news tool.
6. Web search for additional context using the web_search tool (Tavily).

=== Stock Risk Rubric ===
{risk_rubric}

=== Tool Usage Guidelines ===
- Use get_weather for user questions about weather or temperature in a given location.
- Use get_stock_quote when the user asks about a specific ticker (e.g., AAPL, TSLA).
- After calling get_stock_quote, apply the risk rubric above when the user asks whether
  it is low, medium, or high risk. Always mention that this is NOT financial advice.
- Use get_news when the user:
    • Asks for "latest news", "headlines", or "what's happening" in a topic or category.
    • Mentions categories like technology, business, sports, health, science, etc.
    • Asks for updates about companies, events, or people where news is relevant.
- Use web_search when:
    • The user wants more detailed background or context.
    • News results are sparse or missing for a specific question.
    • You need broader web information beyond curated news headlines.

=== Fallback Logic ===
- If get_news returns an error or no relevant articles:
    → Try web_search(query) with a concise query.
- If web_search also fails:
    → Apologize, then answer from your general knowledge.
    → Clearly state that the information may not be fully up to date.

=== Response Style ===
- For news queries:
    • Summarize in concise bullet points.
    • Mention article sources when appropriate (e.g., Reuters, BBC).
    • Do NOT invent URLs. Only use URLs returned by tools.
- For stock queries:
    • Report price, percent change, and brief context.
    • State the risk category and why, using the rubric.
    • Always say that this is not financial advice.
- For weather:
    • Provide temperature, conditions, and any relevant notes (rain, snow, etc.).
- For general questions:
    • Answer directly without calling tools, unless real-time data is clearly needed.

=== Conversation & Memory ===
- You are part of a multi-turn conversation.
- The user may refer back to previous answers (e.g., "now check TSLA" after talking about AAPL).
- Use context from prior turns to interpret pronouns and follow-up questions.

Be helpful, honest, and concise. When in doubt, explain your reasoning clearly.
"""


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
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.2,
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

    # Inject NewsGenie system prompt with the current risk rubric
    system = SystemMessage(
        content=AGENT_SYSTEM_PROMPT.format(risk_rubric=stock_risk_hint())
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
        lc_messages = []
        for m in conv.messages:
            role = m.role
            payload = m.content  # dict we stored
            text = payload.get("text")

            if role == "user":
                lc_messages.append(HumanMessage(content=text))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=text))
            # We skip past tool messages from history; they will be re-created as needed.
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
                    content={
                        "tool_name": msg.name or "tool",
                        "text": str(msg.content),
                    },
                )

        return {
            "conversation_id": conv.id,
            "assistant": last_assistant_text or "",
        }
