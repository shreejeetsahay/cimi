# api/app/models/chat.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ChatSummary(BaseModel):
    id: str
    title: str
    synthesis: str
    recap: str
    project_name: str  # AI suggested project (from LLM)
    project: str  # User specified project (new field)
    tags: List[str] = []
    source_url: str
    platform: str
    created_at: datetime

    class Config:
        # Allow datetime serialization
        json_encoders = {datetime: lambda v: v.isoformat()}
        # Example for API documentation
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Discussion about API Development",
                "synthesis": "Team discussed implementing new API endpoints with focus on error handling and performance optimization.",
                "recap": "# API Development Meeting\n\n## Key Points\n- Discussed error handling strategies\n- Performance optimization priorities\n- Timeline for implementation",
                "project_name": "Web Development",  # AI suggested
                "project": "ChatCards MVP",  # User specified
                "tags": ["API", "Development", "Performance"],
                "source_url": "https://example.com/chat/123",
                "platform": "Slack",
                "created_at": "2025-06-22T10:30:00",
            }
        }
