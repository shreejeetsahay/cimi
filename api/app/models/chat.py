# api/app/models/chat.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class Chat(BaseModel):
    id: str
    title: str
    content: str
    summary: str
    key_insights: List[str]
    source_url: str
    platform: str
    created_at: datetime
    embedding: Optional[List[float]] = None
