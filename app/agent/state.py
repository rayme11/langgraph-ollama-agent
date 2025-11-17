# We’ll define MessagesState / TypedDict here in Step 3 when wiring LangGraph.
from __future__ import annotations
from typing import TypedDict, Annotated, Literal

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

# Our graph state is a list of messages (user/assistant/tool).
# add_messages tells LangGraph how to append new outputs into the list.
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    # Optional “mode” channel if you ever want to branch behavior.
    # mode: Literal["stocks", "weather", "general"]  # example (unused for now)
