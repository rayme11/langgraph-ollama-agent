# -*- coding: utf-8 -*-
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

from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama

from app.agent.state import AgentState
from app.agent.tools import TOOLS, stock_risk_hint
from app.config import get_settings

from app.memory.db import (
    get_session,
    upsert_user,
    create_conversation,
    get_conversation_with_messages,
    append_message,
)

settings = get_settings()


# ---------------------------------------------------------------------
# System prompt for the NewsGenie agent
# ---------------------------------------------------------------------
AGENT_SYSTEM_PROMPT = """
You are NewsGenie, an AI assistant that uses tools to answer questions about
news, weather, stocks, web search, and sports betting.

General rules:
- Always be honest about uncertainty.
- When a user asks for current or factual data (weather, stocks, sports, news, general web info),
  prefer calling tools instead of guessing.
- When a user asks for concepts or explanations that do not depend on live data, you may answer
  directly without tools.
- Keep answers clear, concise, and structured.

Weather:
- Use get_weather to answer questions about current weather or temperature for a city.
- Include location, temperature, feels_like, humidity, and a short description when available.

Stocks:
- Use get_stock_quote when asked about a ticker's current price, change, or percent change.
- When asked to classify a stock as low, medium, or high risk, first call get_stock_quote,
  then use the following rubric:

{stock_risk_hint}

- Always state clearly that stock information is not guaranteed, markets are volatile, and
  this is not financial advice.

Sports betting:
- Users may describe bets in common formats, such as:
  - Team -3.5 (point spread favorite)
  - Team +3.5 (point spread underdog)
  - Moneyline odds like +150 or -180
  - Totals such as over 210.5 or under 6.5

- When a user asks whether a bet is good or requests betting advice for a specific game:
  1) Call get_sports_odds with the appropriate sport and league to fetch current odds and lines.
  2) Call get_team_form for the relevant team(s) with a reasonable days_back (default 5)
     to understand recent performance.
  3) If the bet is a player prop (for example "LeBron over 26.5 points"), also call get_player_form
     for that player and league with a reasonable days_back value.

- Use the odds "price" and any "implied_probability" fields from get_sports_odds to interpret
  how strong a favorite or underdog the bet is.
- Combine recent form (team record, average points for/against, player averages) with
  implied probability to classify the bet into one of these levels:
  - LOW recommendation
  - MEDIUM recommendation
  - HIGH recommendation
  - NOT RECOMMENDED (for missing, conflicting, or very weak data)

- Always explain briefly why you chose that level, referring to:
  - recent record (wins/losses)
  - average margin or scoring
  - relevant player averages
  - the betting line and implied probability
- Always state clearly that sports betting involves risk, outcomes are not guaranteed,
  and this is not financial advice or a guarantee of profit.

News:
- Use get_news when the user asks for headlines, "latest news about X", or category-based
  updates (for example technology, sports, business).
- Summarize the most relevant articles, mentioning titles and sources.
- Do not invent news; rely on tool outputs.

Web search:
- Use web_search when the user needs general web information not covered by the news,
  or when get_news does not address the question well.
- If web_search is disabled or fails, explain that limitation and answer more generally
  only if you have enough context.

Conversation:
- Maintain a friendly, concise tone.
- When you use tool outputs, reference the key numeric fields (prices, percentages, points,
  averages) in your explanation.
- If a tool returns an error, explain it briefly to the user and offer a fallback answer
  if possible.
"""


# ---------------------------------------------------------------------
# Model factory (OpenAI preferred, fallback to local Ollama)
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

    system_text = AGENT_SYSTEM_PROMPT.format(
        stock_risk_hint=stock_risk_hint()
    )
    system = SystemMessage(content=system_text)

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
    conversation_id: Optional[int],
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
            payload = m.content
            text = payload.get("text") if isinstance(payload, dict) else None

            if role == "user":
                lc_messages.append(HumanMessage(content=text))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=text))
            else:
                # Fallback: store as generic AI message
                lc_messages.append(AIMessage(content=str(payload)))

        state: AgentState = {"messages": lc_messages}

        # 3) Run the graph
        result = GRAPH.invoke(state)

        # 4) Persist only the messages produced in this turn (after our prior history)
        new_messages = result["messages"][len(lc_messages):]

        last_assistant_text = None
        for msg in new_messages:
            if isinstance(msg, AIMessage):
                last_assistant_text = (
                    msg.content if isinstance(msg.content, str) else str(msg.content)
                )
                append_message(
                    s,
                    conv,
                    role="assistant",
                    content={"text": last_assistant_text},
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

        return {"conversation_id": conv.id, "assistant": last_assistant_text or ""}
