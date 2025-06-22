# api/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv
from app.services.claude_service import ClaudeService
from app.models.chat import ChatSummary
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


# Request models
class ChatSummarizeRequest(BaseModel):
    chat_content: str
    highlights: Optional[List[str]] = []
    source_url: Optional[str] = ""
    platform: Optional[str] = ""
    tags: Optional[List[str]] = []


@app.get("/")
async def root():
    return {"message": "CIMI API is running"}


@app.post("/api/summarize-chat", response_model=ChatSummary)
async def summarize_chat(request: ChatSummarizeRequest):
    """Summarize chat content with emphasis on highlights."""
    try:
        input_data = {
            "chat_content": request.chat_content,
            "highlights": request.highlights,
            "source_url": request.source_url,
            "platform": request.platform,
            "tags": request.tags,
        }

        summary = await claude_service.summarize_chat(input_data)
        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error summarizing chat: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Check API health."""
    return {"status": "healthy", "service": "chat-summarizer"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
