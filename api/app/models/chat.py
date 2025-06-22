# api/app/models/chat.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class Insight(BaseModel):
    id: str
    type: str  # "code", "knowledge", "solution", "guide"
    content: Optional[str] = None  # Raw text for code
    synthesis: Optional[str] = None  # Summary for knowledge
    problem: Optional[str] = None  # Problem statement for solution
    solution: Optional[str] = None  # Solution description
    context: Optional[str] = None  # Context for solution (e.g., "MySQL")
    title: Optional[str] = None  # Title for guide
    steps: Optional[List[str]] = None  # Steps for guide
    tools: Optional[List[str]] = None  # Tools for guide
    language: Optional[str] = None  # Language for code
    concepts: Optional[List[str]] = None  # Concepts for knowledge
    tags: Optional[List[str]] = None  # User-provided or inferred tags
    project: Optional[str] = None  # User-provided or inferred project
    conversation_id: str
    conversation_title: str
    source_url: str
    platform: str
    created_at: datetime
    embedding: Optional[List[float]] = None  # For Pinecone storage


class ChatSynthesis(BaseModel):
    # Unique ID for the chat session (UUID or from extension).
    id: str
    # Short title for the chat (e.g., "React Debugging Session").
    title: str
    # Brief chat summary (2-3 sentences).
    summary: str
    # List of insights (Code, Knowledge, Solution, Guide) for cards.
    key_insights: List[Insight]
    # URL of the chat (e.g., ChatGPT link).
    source_url: str
    # Platform of the chat (e.g., "chatgpt", "claude").
    platform: str
    # Timestamp when chat was processed (UTC).
    created_at: datetime
