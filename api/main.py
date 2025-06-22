# api/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="ChatCards API", version="1.0.0")

# CORS middleware for Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://*", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class ChatProcessRequest(BaseModel):
    chat_content: str
    source_url: str
    platform: str  # "chatgpt" or "claude"


class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10


class ChatSynthesis(BaseModel):
    id: str
    title: str
    summary: str
    key_insights: List[str]
    source_url: str
    platform: str
    created_at: str


class SearchResult(BaseModel):
    id: str
    title: str
    summary: str
    score: float
    source_url: str


@app.get("/")
async def root():
    return {"message": "ChatCards API is running"}


@app.post("/api/process-chat", response_model=ChatSynthesis)
async def process_chat(request: ChatProcessRequest):
    """Process AI chat and extract key insights"""
    # TODO: Integrate with Claude API for synthesis
    # TODO: Generate embeddings
    # TODO: Store in database
    raise HTTPException(status_code=501, detail="Not implemented yet")


@app.get("/api/search", response_model=List[SearchResult])
async def search_chats(query: str, limit: int = 10):
    """Search processed chats using vector similarity"""
    # TODO: Implement vector search
    # TODO: Return ranked results
    raise HTTPException(status_code=501, detail="Not implemented yet")


@app.get("/api/chat/{chat_id}", response_model=ChatSynthesis)
async def get_chat_details(chat_id: str):
    """Get detailed chat information by ID"""
    # TODO: Retrieve from database
    raise HTTPException(status_code=501, detail="Not implemented yet")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
