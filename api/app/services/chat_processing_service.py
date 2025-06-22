# app/services/chat_processing_service.py
from app.services.claude_service import ClaudeService
from app.services.database_service import DatabaseService
from app.services.pinecone_service import PineconeService
from app.models.chat import ChatSummary
from typing import Dict, Any


class ChatProcessingService:
    def __init__(self):
        self.claude_service = ClaudeService()
        self.db_service = DatabaseService()
        self.pinecone_service = PineconeService()

    async def process_and_store_chat(self, input_data: Dict[str, Any]) -> ChatSummary:
        """Complete pipeline: LLM processing → Database storage → Pinecone embedding."""

        # Step 1: Process with Claude (your existing functionality)
        summary = await self.claude_service.summarize_chat(input_data)

        # Step 2: Store in database (with overwrite logic)
        success = self.db_service.save_chat_summary(summary)
        if not success:
            raise Exception("Failed to save chat summary to database")

        # Step 3: Store embedding in Pinecone
        embedding_success = self.pinecone_service.store_embedding(summary)
        if not embedding_success:
            print(f"Warning: Failed to store embedding for chat {summary.id}")
            # Don't fail the whole operation, just log the warning

        return summary

    def chat_exists(self, source_url: str) -> bool:
        """Check if chat already exists."""
        return self.db_service.chat_exists(source_url)

    def get_chat_by_id(self, chat_id: str) -> ChatSummary:
        """Get a specific chat by ID."""
        result = self.db_service.get_chat_by_id(chat_id)
        if not result:
            raise Exception(f"Chat with ID {chat_id} not found")

        # Convert SearchResult back to ChatSummary
        return ChatSummary(
            id=result.id,
            title=result.title,
            synthesis=result.synthesis,
            recap=result.recap,
            project_name=result.project_name,
            tags=result.tags,
            source_url=result.source_url,
            platform=result.platform,
            created_at=result.created_at,
        )
