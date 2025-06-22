# app/services/search_service.py
import time
from typing import List
from app.services.database_service import DatabaseService
from app.services.pinecone_service import PineconeService
from app.models.search import SearchRequest, SearchResponse, SearchResult


class SearchService:
    def __init__(self):
        self.db_service = DatabaseService()
        self.pinecone_service = PineconeService()

    def search(self, request: SearchRequest) -> SearchResponse:
        """Perform combined semantic + keyword search."""
        start_time = time.time()

        print(f"Searching for: '{request.query}'")

        # Perform both searches
        print("Performing keyword search...")
        keyword_results = self.db_service.keyword_search(request)
        print(f"Keyword search found {len(keyword_results)} results")

        print("Performing semantic search...")
        semantic_results = self._get_semantic_results(request)
        print(f"Semantic search found {len(semantic_results)} results")

        # Combine and deduplicate results
        combined_results = self._combine_results(semantic_results, keyword_results)
        print(f"Combined search found {len(combined_results)} unique results")

        # Calculate search time
        search_time_ms = int((time.time() - start_time) * 1000)

        return SearchResponse(
            results=combined_results[: request.limit],
            total_count=len(combined_results),
            query=request.query,
            search_time_ms=search_time_ms,
        )

    def _get_semantic_results(self, request: SearchRequest) -> List[SearchResult]:
        """Get semantic search results from Pinecone (placeholder for now)."""
        if not self.pinecone_service.enabled:
            print("Pinecone not enabled, skipping semantic search")
            return []

        print("Performing semantic search...")
        pinecone_matches = self.pinecone_service.semantic_search(request)

        semantic_results = []
        for match in pinecone_matches:
            # Get full chat data from database using the ID
            chat_data = self.db_service.get_chat_by_id(match["id"])
            if chat_data:
                chat_data.relevance_score = match["score"]
                chat_data.search_type = "semantic"
                semantic_results.append(chat_data)

        print(f"Semantic search found {len(semantic_results)} results")
        return semantic_results

    def _combine_results(
        self, semantic_results: List[SearchResult], keyword_results: List[SearchResult]
    ) -> List[SearchResult]:
        """Combine and deduplicate search results."""
        # Create a dict to track unique results by source_url
        results_dict = {}

        # Add semantic results first (higher priority)
        for result in semantic_results:
            results_dict[result.source_url] = result

        # Add keyword results if not already present
        for result in keyword_results:
            if result.source_url not in results_dict:
                results_dict[result.source_url] = result

        # Convert back to list and sort by relevance/date
        combined_results = list(results_dict.values())

        # Sort: semantic results with high scores first, then by date
        def sort_key(result):
            if result.search_type == "semantic" and result.relevance_score:
                return (0, -result.relevance_score)  # Higher scores first
            else:
                return (1, -result.created_at.timestamp())  # More recent first

        combined_results.sort(key=sort_key)
        return combined_results
