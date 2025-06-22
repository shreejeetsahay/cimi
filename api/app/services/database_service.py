# app/services/database_service.py
import sqlite3
import json
from typing import List, Optional
from datetime import datetime
from app.models.chat import ChatSummary
from app.models.search import SearchResult, SearchRequest


class DatabaseService:
    def __init__(self, db_path: str = "chatcards.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize SQLite database with chat summaries table."""
        with sqlite3.connect(self.db_path) as conn:
            # First, check if we need to add the project column
            cursor = conn.execute("PRAGMA table_info(chat_summaries)")
            columns = [row[1] for row in cursor.fetchall()]

            if "project" not in columns:
                # Add the project column to existing table
                print("Adding 'project' column to existing chat_summaries table...")
                conn.execute(
                    "ALTER TABLE chat_summaries ADD COLUMN project TEXT DEFAULT 'General'"
                )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_summaries (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    synthesis TEXT NOT NULL,
                    recap TEXT NOT NULL,
                    project_name TEXT NOT NULL,  -- AI suggested project
                    project TEXT NOT NULL DEFAULT 'General',  -- User specified project
                    tags TEXT NOT NULL,  -- JSON array
                    source_url TEXT UNIQUE NOT NULL,
                    platform TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """
            )

            # Create indexes for search performance
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_title ON chat_summaries(title)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_project_name ON chat_summaries(project_name)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_project ON chat_summaries(project)"
            )  # New index
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_platform ON chat_summaries(platform)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_source_url ON chat_summaries(source_url)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_created_at ON chat_summaries(created_at)"
            )

    def save_chat_summary(self, summary: ChatSummary) -> bool:
        """Save or update chat summary (Option 2: Always Overwrite)."""
        with sqlite3.connect(self.db_path) as conn:
            # Delete existing record if it exists
            conn.execute(
                "DELETE FROM chat_summaries WHERE source_url = ?", (summary.source_url,)
            )

            # Insert new record
            conn.execute(
                """
                INSERT INTO chat_summaries 
                (id, title, synthesis, recap, project_name, project, tags, source_url, platform, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    summary.id,
                    summary.title,
                    summary.synthesis,
                    summary.recap,
                    summary.project_name,
                    summary.project,  # Add user project
                    json.dumps(summary.tags),
                    summary.source_url,
                    summary.platform,
                    summary.created_at.isoformat(),
                ),
            )
            return True

    def keyword_search(self, request: SearchRequest) -> List[SearchResult]:
        """Perform keyword search on metadata."""
        query_parts = []
        params = []

        # Base search query
        base_query = """
            SELECT id, title, synthesis, recap, project_name, project, tags, 
                   source_url, platform, created_at
            FROM chat_summaries WHERE 1=1
        """

        # Add text search
        if request.query.strip():
            query_parts.append(
                """
                AND (title LIKE ? OR synthesis LIKE ? OR tags LIKE ?)
            """
            )
            search_term = f"%{request.query}%"
            params.extend([search_term, search_term, search_term])

        # Add filters
        if request.project_filter:
            query_parts.append("AND project_name = ?")
            params.append(request.project_filter)

        if request.platform_filter:
            query_parts.append("AND platform = ?")
            params.append(request.platform_filter)

        if request.date_from:
            query_parts.append("AND created_at >= ?")
            params.append(request.date_from.isoformat())

        if request.date_to:
            query_parts.append("AND created_at <= ?")
            params.append(request.date_to.isoformat())

        # Complete query
        full_query = (
            base_query + "".join(query_parts) + " ORDER BY created_at DESC LIMIT ?"
        )
        params.append(request.limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(full_query, params)
            rows = cursor.fetchall()

        results = []
        for row in rows:
            results.append(
                SearchResult(
                    id=row["id"],
                    title=row["title"],
                    synthesis=row["synthesis"],
                    recap=row["recap"],
                    project_name=row["project_name"],
                    tags=json.loads(row["tags"]),
                    source_url=row["source_url"],
                    platform=row["platform"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    search_type="keyword",
                )
            )

        return results

    def get_chat_by_id(self, chat_id: str) -> Optional[SearchResult]:
        """Get a specific chat by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT id, title, synthesis, recap, project_name, tags, 
                       source_url, platform, created_at
                FROM chat_summaries WHERE id = ?
            """,
                (chat_id,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        return SearchResult(
            id=row["id"],
            title=row["title"],
            synthesis=row["synthesis"],
            recap=row["recap"],
            project_name=row["project_name"],
            tags=json.loads(row["tags"]),
            source_url=row["source_url"],
            platform=row["platform"],
            created_at=datetime.fromisoformat(row["created_at"]),
            search_type="direct",
        )

    def chat_exists(self, source_url: str) -> bool:
        """Check if a chat with this source URL already exists."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM chat_summaries WHERE source_url = ?", (source_url,)
            )
            return cursor.fetchone() is not None
