# api/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from app.services.claude_service import ClaudeService
from app.models.chat import ChatSynthesis, Insight
from sentence_transformers import SentenceTransformer
import uvicorn

load_dotenv()

app = FastAPI(title="CIMI API", version="1.0.0")

# CORS middleware for Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://*", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
claude_service = ClaudeService()
embedder = SentenceTransformer("all-MiniLM-L6-v2")


# Request models
class ChatProcessRequest(BaseModel):
    chat_content: str
    source_url: str
    platform: str  # "chatgpt" or "claude"
    project: Optional[str] = None
    tags: Optional[List[str]] = None
    conversation_id: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10


class SearchResult(BaseModel):
    id: str
    type: str
    title: str
    summary: str
    score: float
    source_url: str
    project: Optional[str]
    conversation_id: str
    conversation_title: str


@app.get("/")
async def root():
    return {"message": "ChatCards API is running"}


@app.post("/api/process-chat", response_model=ChatSynthesis)
async def process_chat(request: ChatProcessRequest):
    """Process AI chat or highlighted text and extract insights."""
    try:
        # Process chat using Claude
        synthesis = await claude_service.synthesize_chat(
            chat_content=request.chat_content,
            source_url=request.source_url,
            platform=request.platform,
            project=request.project,
            tags=request.tags,
            conversation_id=request.conversation_id,
        )

        # Generate embeddings for each insight
        for insight in synthesis.key_insights:
            text_to_embed = (
                insight.content
                or insight.synthesis
                or insight.solution
                or " ".join(insight.steps or [])
                or insight.title
                or ""
            )
            insight.embedding = embedder.encode(text_to_embed).tolist()

        # Return synthesis for storage in Pinecone (handled by your friend)
        return synthesis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


@app.get("/api/search", response_model=List[SearchResult])
async def search_chats(query: str, limit: int = 10):
    """Search insights using vector similarity (placeholder for Pinecone)."""
    # Placeholder: Your friend will implement Pinecone search
    # For now, return mock results
    raise HTTPException(
        status_code=501, detail="Search not implemented yet (handled by Pinecone team)"
    )


@app.get("/api/chat/{chat_id}", response_model=ChatSynthesis)
async def get_chat_details(chat_id: str):
    """Get detailed chat information by ID (placeholder for Pinecone)."""
    # Placeholder: Your friend will implement Pinecone retrieval
    raise HTTPException(
        status_code=501,
        detail="Chat retrieval not implemented yet (handled by Pinecone team)",
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
