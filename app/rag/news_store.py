from __future__ import annotations

"""
RAG support for live news in NewsGenie.

This module provides:
  - A Chroma vector store persisted on disk
  - OpenAI-based embeddings
  - Helpers to index news articles
  - Helpers to retrieve semantically relevant past news

It is intentionally decoupled so it can be called from:
  - tools (e.g., after get_news)
  - the agent (for follow-up questions)
"""

import os
from typing import List, Dict, Any, Optional

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from app.config import get_settings

settings = get_settings()

# Module-level cache for the vector store
_news_vectorstore: Optional[Chroma] = None


def _get_embeddings():
    """
    Return an OpenAI embeddings instance.

    Uses:
      - OPENAI_API_KEY (from Settings)
      - OPENAI_EMBEDDINGS_MODEL env var or Settings default

    Raises:
      RuntimeError if the OpenAI API key is missing.
    """
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing. "
            "News RAG requires OpenAI embeddings for now."
        )

    model_name = getattr(settings, "openai_embeddings_model", None) or os.getenv(
        "OPENAI_EMBEDDINGS_MODEL",
        "text-embedding-3-small",
    )
    return OpenAIEmbeddings(model=model_name)


def _get_news_vectorstore() -> Chroma:
    """
    Lazily initialize and return the Chroma vector store for news.

    The store is persisted in a directory, e.g. ./rag_news_db or RAG_NEWS_DB_PATH.
    """
    global _news_vectorstore
    if _news_vectorstore is not None:
        return _news_vectorstore

    persist_dir = getattr(settings, "rag_news_db_path", None) or os.getenv(
        "RAG_NEWS_DB_PATH",
        "./rag_news_db",
    )

    embeddings = _get_embeddings()

    # Initialize (or load) a persistent Chroma collection
    _news_vectorstore = Chroma(
        collection_name="newsgenie_news",
        embedding_function=embeddings,
        persist_directory=persist_dir,
    )
    return _news_vectorstore


def index_news_batch(
    articles: List[Dict[str, Any]],
    *,
    category: Optional[str] = None,
    query: Optional[str] = None,
    conversation_id: Optional[int] = None,
    user_id: Optional[str] = None,
) -> int:
    """
    Index a batch of news articles into the RAG store.

    Typically called after a successful get_news() tool call.

    Args:
        articles: List of article dicts, e.g. from get_news:
                  [
                    {
                      "title": ...,
                      "desc": ...,
                      "url": ...,
                      "source": ...,
                      "published_at": ...
                    },
                    ...
                  ]
        category: News category (general, technology, business, etc.)
        query:    Original user/topic query, if any
        conversation_id: Optional link to the DB conversation for context
        user_id:  Optional external_user_id

    Returns:
        int: Number of articles successfully indexed.
    """
    if not articles:
        return 0

    try:
        vs = _get_news_vectorstore()
    except RuntimeError:
        # No embeddings / key → skip indexing gracefully
        return 0

    docs: List[Document] = []
    for art in articles:
        title = art.get("title") or ""
        desc = art.get("desc") or art.get("description") or ""
        url = art.get("url")
        source_name = art.get("source")
        published_at = art.get("published_at")

        # Build a concise but informative content string
        content = f"{title}\n\n{desc}"
        if source_name:
            content += f"\n\nSource: {source_name}"

        metadata: Dict[str, Any] = {
            "url": url,
            "source": source_name,
            "published_at": published_at,
            "category": category,
            "query": query,
        }
        if conversation_id is not None:
            metadata["conversation_id"] = conversation_id
        if user_id is not None:
            metadata["user_id"] = user_id

        docs.append(Document(page_content=content, metadata=metadata))

    if not docs:
        return 0

    vs.add_documents(docs)
    vs.persist()

    return len(docs)


def retrieve_relevant_news(
    query: str,
    k: int = 5,
    *,
    conversation_id: Optional[int] = None,
    user_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve semantically relevant past news articles for a query.

    Args:
        query: User's query text (for semantic similarity).
        k:     Maximum number of hits to return.
        conversation_id: Optional filter by conversation.
        user_id:          Optional filter by user.

    Returns:
        List of dicts with:
          - "content": combined title/desc/source text
          - metadata fields: url, source, published_at, category, query, etc.
    """
    if not query.strip():
        return []

    try:
        vs = _get_news_vectorstore()
    except RuntimeError:
        # No embeddings configured → retrieval not available
        return []

    # Base retrieval
    docs = vs.similarity_search(query, k=k)

    # Optional filtering post-retrieval by conversation_id / user_id
    filtered: List[Dict[str, Any]] = []
    for d in docs:
        md = d.metadata or {}
        if conversation_id is not None and md.get("conversation_id") != conversation_id:
            continue
        if user_id is not None and md.get("user_id") != user_id:
            continue

        entry: Dict[str, Any] = {
            "content": d.page_content,
        }
        entry.update(md)
        filtered.append(entry)

    return filtered
