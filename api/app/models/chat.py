# api/app/models/chat.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ChatSummary(BaseModel):
    id: str
    title: str
    synthesis: str
    recap: str
    project_name: str  # Just the final project (starts with AI suggestion)
    tags: List[str] = []
    source_url: str
    platform: str
    created_at: datetime
