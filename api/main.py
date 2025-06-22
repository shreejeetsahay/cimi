# api/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from app.services.claude_service import ClaudeService
from app.models.chat import ChatSynthesis, Insight
from database.vectors import Vectors
from sentence_transformers import SentenceTransformer
import uvicorn
import uuid

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

# Initialize Vectors service
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY environment variable is required")

vector_service = Vectors(api_key=PINECONE_API_KEY)

# Configuration
INDEX_NAME = "cimi-insights"
NAMESPACE = "chat-insights"
EMBEDDING_DIMENSION = 384  # all-MiniLM-L6-v2 dimension


# Database initialization
@app.on_event("startup")
async def initialize_database():
    """Initialize Pinecone index on startup if it doesn't exist."""
    try:
        vector_service.create_index(
            index_name=INDEX_NAME,
            dimension=EMBEDDING_DIMENSION,
            metric="cosine",
            vector_type="dense",
            cloud={"name": "aws", "region": "us-east-1"},
            deletion_protection="disabled",
            tags={"environment": "development", "project": "cimi"},
        )
        print(f"✅ Pinecone index '{INDEX_NAME}' ready")
    except Exception as e:
        print(f"⚠️ Error initializing Pinecone index: {e}")


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
    project: Optional[str] = None
    platform: Optional[str] = None


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

        # Prepare vectors for upsert
        vectors_to_upsert = []

        # Generate embeddings for each insight and prepare for Pinecone
        for insight in synthesis.key_insights:
            text_to_embed = (
                insight.content
                or insight.synthesis
                or insight.solution
                or " ".join(insight.steps or [])
                or insight.title
                or ""
            )

            # Generate embedding
            embedding = embedder.encode(text_to_embed).tolist()
            insight.embedding = embedding

            # Create unique ID for this insight
            insight_id = str(uuid.uuid4())

            # Prepare metadata
            metadata = {
                "type": insight.type,
                "title": insight.title,
                "content": text_to_embed[:1000],  # Truncate for metadata
                "source_url": request.source_url,
                "platform": request.platform,
                "project": request.project,
                "conversation_id": request.conversation_id or "",
                "conversation_title": synthesis.conversation_title,
                "tags": request.tags or [],
                "created_at": (
                    synthesis.timestamp.isoformat() if synthesis.timestamp else ""
                ),
            }

            # Add to vectors list
            vectors_to_upsert.append(
                {"id": insight_id, "values": embedding, "metadata": metadata}
            )

        # Upsert vectors to Pinecone
        if vectors_to_upsert:
            vector_service.upsert_vectors(
                index_name=INDEX_NAME, namespace=NAMESPACE, vectors=vectors_to_upsert
            )
            print(f"✅ Upserted {len(vectors_to_upsert)} insights to Pinecone")

        return synthesis

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


@app.get("/api/search", response_model=List[SearchResult])
async def search_chats(
    query: str,
    limit: int = 10,
    project: Optional[str] = None,
    platform: Optional[str] = None,
):
    """Search insights using vector similarity."""
    try:
        # Generate embedding for search query
        query_embedding = embedder.encode(query).tolist()

        # Build filter if needed
        search_filter = {}
        if project:
            search_filter["project"] = {"$eq": project}
        if platform:
            search_filter["platform"] = {"$eq": platform}

        # Perform similarity search
        results = vector_service.similarity_search(
            index_name=INDEX_NAME,
            namespace=NAMESPACE,
            query_vector=query_embedding,
            no_of_results=limit,
            filter=search_filter if search_filter else None,
        )

        if results == -1:
            raise HTTPException(status_code=404, detail="Index not found")

        # Convert to SearchResult format
        search_results = []
        for match in results.get("matches", []):
            metadata = match.get("metadata", {})
            search_results.append(
                SearchResult(
                    id=match["id"],
                    type=metadata.get("type", "insight"),
                    title=metadata.get("title", "Untitled"),
                    summary=metadata.get("content", "")[:200] + "...",
                    score=match["score"],
                    source_url=metadata.get("source_url", ""),
                    project=metadata.get("project"),
                    conversation_id=metadata.get("conversation_id", ""),
                    conversation_title=metadata.get("conversation_title", ""),
                )
            )

        return search_results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching: {str(e)}")


@app.get("/api/chat/{chat_id}", response_model=ChatSynthesis)
async def get_chat_details(chat_id: str):
    """Get detailed chat information by ID."""
    # This would require storing full chat synthesis objects
    # For now, we can search by conversation_id
    try:
        results = vector_service.similarity_search(
            index_name=INDEX_NAME,
            namespace=NAMESPACE,
            query_vector=[0.0] * EMBEDDING_DIMENSION,  # Dummy vector
            no_of_results=100,
            filter={"conversation_id": {"$eq": chat_id}},
        )

        if not results or not results.get("matches"):
            raise HTTPException(status_code=404, detail="Chat not found")

        # This is a simplified response - you might want to reconstruct the full ChatSynthesis
        # or store it separately for complete retrieval
        raise HTTPException(
            status_code=501,
            detail="Full chat retrieval needs additional implementation",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chat: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Check API and Pinecone connection health."""
    try:
        # Check if index exists
        index_exists = vector_service.pc.has_index(INDEX_NAME)
        return {
            "status": "healthy",
            "pinecone_connected": True,
            "index_exists": index_exists,
            "index_name": INDEX_NAME,
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "pinecone_connected": False}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
