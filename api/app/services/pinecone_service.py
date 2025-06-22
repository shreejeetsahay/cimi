# app/services/pinecone_service.py
import os
from typing import List, Dict, Any
from app.models.chat import ChatSummary
from app.models.search import SearchRequest

# Only import pinecone if the API key is available
try:
    from pinecone import Pinecone

    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    print("Warning: Pinecone not installed. Semantic search will be disabled.")


class PineconeService:
    def __init__(self):
        self.enabled = False

        # Check if Pinecone is available and configured
        if not PINECONE_AVAILABLE:
            print("Pinecone service disabled: library not available")
            return

        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            print("Pinecone service disabled: PINECONE_API_KEY not set")
            return

        try:
            # Initialize Pinecone client
            self.pc = Pinecone(api_key=api_key)
            self.index_name = "chatcards"
            self.namespace = "chat-summaries"

            # Create index with integrated embedding model if it doesn't exist
            if not self.pc.has_index(self.index_name):
                print(f"Creating Pinecone index: {self.index_name}")
                self.pc.create_index_for_model(
                    name=self.index_name,
                    cloud="aws",
                    region="us-east-1",
                    embed={
                        "model": "multilingual-e5-large",  # Good general-purpose model
                        "field_map": {
                            "text": "content"
                        },  # Map our 'content' field to embeddings
                    },
                )

            self.index = self.pc.Index(self.index_name)
            self.enabled = True
            print("Pinecone service initialized successfully")

        except Exception as e:
            print(f"Failed to initialize Pinecone: {e}")
            print("Semantic search will be disabled")

    def prepare_content_text(self, summary: ChatSummary) -> str:
        """Prepare text for embedding: title + synthesis + tags."""
        tags_text = " ".join(summary.tags)
        return f"{summary.title} {summary.synthesis} {tags_text}"

    def store_embedding(self, summary: ChatSummary) -> bool:
        """Store chat summary in Pinecone using integrated embeddings."""
        if not self.enabled:
            print("Pinecone not enabled, skipping embedding storage")
            return False

        try:
            # Delete existing record first (Option 2: Always Overwrite)
            self.delete_embedding_by_source_url(summary.source_url)

            # Prepare record for upsert
            content_text = self.prepare_content_text(summary)

            record = {
                "_id": summary.id,
                "content": content_text,  # This gets embedded automatically
                "title": summary.title,
                "synthesis": summary.synthesis,
                "source_url": summary.source_url,
                "project_name": summary.project_name,
                "platform": summary.platform,
                "created_at": summary.created_at.isoformat(),
                "tags": summary.tags,
            }

            # Upsert using new API
            self.index.upsert_records(self.namespace, [record])
            print(f"Stored embedding for chat: {summary.title}")
            return True

        except Exception as e:
            print(f"Error storing embedding: {e}")
            return False

    def delete_embedding_by_source_url(self, source_url: str):
        """Delete existing embeddings with this source_url."""
        if not self.enabled:
            return

        try:
            # Search for existing records with this source_url
            search_results = self.index.search(
                namespace=self.namespace,
                query={
                    "top_k": 100,
                    "inputs": {"text": "dummy"},  # Dummy query
                    "filter": {"source_url": source_url},
                },
            )

            # Extract IDs to delete
            if "result" in search_results and "hits" in search_results["result"]:
                ids_to_delete = [hit["_id"] for hit in search_results["result"]["hits"]]

                if ids_to_delete:
                    self.index.delete(ids=ids_to_delete, namespace=self.namespace)
                    print(
                        f"Deleted {len(ids_to_delete)} existing embeddings for {source_url}"
                    )

        except Exception as e:
            print(f"Error deleting embeddings: {e}")

    def semantic_search(self, request: SearchRequest) -> List[Dict[str, Any]]:
        """Perform semantic search using Pinecone's integrated embeddings."""
        if not self.enabled:
            print("Pinecone not enabled, returning empty semantic results")
            return []

        try:
            # Build filter
            filter_dict = {}
            if request.project_filter:
                filter_dict["project_name"] = request.project_filter
            if request.platform_filter:
                filter_dict["platform"] = request.platform_filter

            # Search using new API
            if not filter_dict:
                search_results = self.index.search(
                    namespace=self.namespace,
                    query={
                        "top_k": request.limit,
                        "inputs": {"text": request.query},
                        # "filter": filter_dict if filter_dict else None,
                    },
                )
            else:
                search_results = self.index.search(
                    namespace=self.namespace,
                    query={
                        "top_k": request.limit,
                        "inputs": {"text": request.query},
                        "filter": filter_dict
                    },
                )

            

            # Convert results to our expected format
            matches = []
            if "result" in search_results and "hits" in search_results["result"]:
                for hit in search_results["result"]["hits"]:
                    matches.append(
                        {
                            "id": hit["_id"],
                            "score": hit["_score"],
                            "metadata": {
                                "source_url": hit["fields"].get("source_url"),
                                "title": hit["fields"].get("title"),
                                "project_name": hit["fields"].get("project_name"),
                                "platform": hit["fields"].get("platform"),
                                "created_at": hit["fields"].get("created_at"),
                            },
                        }
                    )

            print(f"Semantic search found {len(matches)} results")
            return matches

        except Exception as e:
            print(f"Error in semantic search: {e}")
            return []

    def get_vector_count(self) -> int:
        """Get count of stored vectors."""
        if not self.enabled:
            return 0

        try:
            stats = self.index.describe_index_stats()
            if "namespaces" in stats and self.namespace in stats["namespaces"]:
                return stats["namespaces"][self.namespace]["vector_count"]
            return 0
        except Exception as e:
            print(f"Error getting vector count: {e}")
            return 0
