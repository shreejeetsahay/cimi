from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from app.services.chat_processing_service import ChatProcessingService
from app.services.search_service import SearchService
from app.models.chat import ChatSummary
from app.models.search import SearchRequest, SearchResponse
import uvicorn

# Load environment variables
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
chat_processing_service = ChatProcessingService()
search_service = SearchService()


# Request models
class ChatSummarizeRequest(BaseModel):
    chat_content: str
    highlights: Optional[List[str]] = []
    source_url: Optional[str] = ""
    platform: Optional[str] = ""
    tags: Optional[List[str]] = []
    project: Optional[str] = "General"  # Add project field with default
    verbose: Optional[bool] = False


@app.get("/")
async def root():
    return {"message": "CIMI API is running"}


@app.post("/api/summarize-chat", response_model=ChatSummary)
async def summarize_chat(request: ChatSummarizeRequest):
    """Process chat with LLM and store in database + Pinecone."""
    try:
        input_data = {
            "chat_content": request.chat_content,
            "highlights": request.highlights,
            "source_url": request.source_url,
            "platform": request.platform,
            "tags": request.tags,
            "project": request.project,  # Add user project
            "verbose": request.verbose,  # Pass verbose flag
        }

        # Full pipeline: LLM → Database → Pinecone
        summary = await chat_processing_service.process_and_store_chat(input_data)
        return summary

    except Exception as e:
        print(f"Error in summarize_chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


@app.get("/api/chats", response_model=List[ChatSummary])
async def get_all_chats(limit: Optional[int] = 100, offset: Optional[int] = 0):
    """Get all stored chats with pagination."""
    try:
        import sqlite3

        with sqlite3.connect("chatcards.db") as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT id, title, synthesis, recap, project_name, 
                       COALESCE(project, 'General') as project, tags, 
                       source_url, platform, created_at
                FROM chat_summaries 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """,
                (limit, offset),
            )
            rows = cursor.fetchall()

            results = []
            for row in rows:
                results.append(
                    ChatSummary(
                        id=row["id"],
                        title=row["title"],
                        synthesis=row["synthesis"],
                        recap=row["recap"],
                        project_name=row["project_name"],
                        project=row["project"],  # This will be 'General' if NULL
                        tags=json.loads(row["tags"]),
                        source_url=row["source_url"],
                        platform=row["platform"],
                        created_at=datetime.fromisoformat(row["created_at"]),
                    )
                )

            return results

    except Exception as e:
        print(f"Error getting all chats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching chats: {str(e)}")


@app.get("/api/chats/count")
async def get_chats_count():
    """Get total count of stored chats."""
    try:
        import sqlite3

        with sqlite3.connect("chatcards.db") as conn:
            cursor = conn.execute("SELECT COUNT(*) as count FROM chat_summaries")
            row = cursor.fetchone()
            return {"count": row[0]}

    except Exception as e:
        print(f"Error getting chat count: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting count: {str(e)}")


@app.post("/api/search", response_model=SearchResponse)
async def search_chats(request: SearchRequest):
    """Search through stored chat summaries."""
    try:
        results = search_service.search(request)
        return results

    except Exception as e:
        print(f"Error in search endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching chats: {str(e)}")


@app.get("/api/search-test")
async def search_test():
    """Simple test search endpoint."""
    try:
        test_request = SearchRequest(query="React", limit=5)
        results = search_service.search(test_request)
        return {"message": "Search working", "count": results.total_count}

    except Exception as e:
        return {"error": str(e)}


@app.get("/api/chat/{chat_id}", response_model=ChatSummary)
async def get_chat(chat_id: str):
    """Get a specific chat by ID."""
    try:
        chat = chat_processing_service.get_chat_by_id(chat_id)
        return chat

    except Exception as e:
        print(f"Error getting chat {chat_id}: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Chat not found: {str(e)}")


@app.get("/api/chat-exists")
async def check_chat_exists(source_url: str):
    """Check if a chat with this source URL already exists."""
    try:
        exists = chat_processing_service.chat_exists(source_url)
        return {"exists": exists, "source_url": source_url}

    except Exception as e:
        print(f"Error checking chat existence: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error checking chat: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Check API health."""
    return {"status": "healthy", "service": "chat-summarizer"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
