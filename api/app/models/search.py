# app/models/search.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class SearchResult(BaseModel):
    id: str
    title: str
    synthesis: str
    recap: str
    project_name: str
    tags: List[str]
    source_url: str
    platform: str
    created_at: datetime
    relevance_score: Optional[float] = None
    search_type: str  # "semantic" or "keyword"


class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10
    project_filter: Optional[str] = None
    platform_filter: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total_count: int
    query: str
    search_time_ms: int
