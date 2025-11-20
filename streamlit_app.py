from __future__ import annotations

import uuid
from typing import Dict, Any

import streamlit as st

from app.agent.graph import run_agent_turn
from app.memory.db import init_db


# ------------------------------------------------------------
# Initial setup
# ------------------------------------------------------------
def ensure_db():
    if "db_initialized" not in st.session_state:
        init_db()
        st.session_state["db_initialized"] = True


def get_default_user_id() -> str:
    # Simple per-browser session user id generator
    if "external_user_id" not in st.session_state:
        st.session_state["external_user_id"] = f"anon-{uuid.uuid4()}"
    return st.session_state["external_user_id"]


def get_conversation_id() -> int | None:
    return st.session_state.get("conversation_id")


def set_conversation_id(cid: int):
    st.session_state["conversation_id"] = cid


def get_chat_history() -> list[Dict[str, Any]]:
    """
    Keeps a simple list of messages:
      [{"role": "user"|"assistant", "content": "..."}]
    This is only for display; the real memory is in SQLite via run_agent_turn.
    """
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    return st.session_state["chat_history"]


def append_to_chat(role: str, content: str):
    history = get_chat_history()
    history.append({"role": role, "content": content})
    st.session_state["chat_history"] = history


# ------------------------------------------------------------
# Streamlit UI layout
# ------------------------------------------------------------
def main():
    st.set_page_config(
        page_title="NewsGenie – AI News & Info Assistant",
        page_icon="🧠",
        layout="wide",
    )

    ensure_db()

    st.title("🧠 NewsGenie")
    st.caption(
        "AI-powered assistant for **news**, **stocks**, **weather**, and **web search** "
        "using LangGraph, local/remote LLMs, and real APIs."
    )

    # Sidebar: session + preferences
    with st.sidebar:
        st.header("Session & Preferences")

        # User identity
        external_user_id = st.text_input(
            "User ID (email or alias)",
            value=get_default_user_id(),
            help="Used to tie your conversations to a logical user in the DB.",
        )
        st.session_state["external_user_id"] = external_user_id

        # News category preference
        news_category = st.selectbox(
            "Preferred news category (optional)",
            options=[
                "auto-detect",
                "general",
                "business",
                "technology",
                "sports",
                "science",
                "health",
                "entertainment",
            ],
            index=0,
            help=(
                "If set, NewsGenie will treat many queries as news-related in this category "
                "and may call the news tool accordingly."
            ),
        )
        st.session_state["news_category"] = news_category

        st.markdown("---")
        if st.button("🧹 Start New Conversation"):
            st.session_state.pop("conversation_id", None)
            st.session_state["chat_history"] = []
            st.success("Started a new conversation.")

        st.markdown("### Tips")
        st.markdown(
            "- Ask: **“Latest AI tech news?”**\n"
            "- Ask: **“Weather in Austin,US?”**\n"
            "- Ask: **“Check AAPL risk today”**\n"
            "- Ask: **“Search web for SpaceX launch details”**"
        )

    # Main chat area
    chat_history = get_chat_history()
    for message in chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input
    user_prompt = st.chat_input("Ask NewsGenie something…")
    if user_prompt:
        external_user_id = st.session_state["external_user_id"]
        conversation_id = get_conversation_id()
        news_category = st.session_state.get("news_category", "auto-detect")

        # Display user message
        append_to_chat("user", user_prompt)
        with st.chat_message("user"):
            st.markdown(user_prompt)

        # Optionally inject lightweight category hint to help the agent
        if news_category != "auto-detect":
            enriched_prompt = (
                f"[User prefers news category: {news_category}] {user_prompt}"
            )
        else:
            enriched_prompt = user_prompt

        # Call the LangGraph agent
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = run_agent_turn(
                    external_user_id=external_user_id,
                    conversation_id=conversation_id,
                    user_text=enriched_prompt,
                )
                assistant_text = result.get("assistant", "")
                new_conv_id = result.get("conversation_id")
                if new_conv_id is not None:
                    set_conversation_id(new_conv_id)

                st.markdown(assistant_text)
                append_to_chat("assistant", assistant_text)


if __name__ == "__main__":
    main()
