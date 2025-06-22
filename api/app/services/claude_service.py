# api/app/services/claude_service.py
import anthropic
import os
import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import uuid4
from app.models.chat import Insight, ChatSynthesis


class ClaudeService:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async def synthesize_chat(
        self,
        chat_content: str,
        source_url: str,
        platform: str,
        project: Optional[str] = None,
        tags: Optional[List[str]] = None,
        conversation_id: Optional[str] = None,
    ) -> ChatSynthesis:
        """Process chat content or highlighted text into structured insights."""
        # Generate conversation_id if not provided
        conversation_id = conversation_id or str(uuid4())

        # Heuristics for segmenting and feature detection
        segments = self._segment_content(chat_content)
        # this is similiar to the rag approach of chunking.
        # may be unecessary, but also a splitting criteria makes so much sense.

        insights = []

        # Process each segment
        for segment in segments:
            insight = await self._process_segment(
                segment=segment,
                platform=platform,
                source_url=source_url,
                conversation_id=conversation_id,
                project=project,
                tags=tags,
            )
            insights.append(insight)

        # Generate high-level chat metadata
        chat_title, chat_summary = await self._generate_chat_metadata(chat_content)

        return ChatSynthesis(
            id=conversation_id,
            title=chat_title,
            summary=chat_summary,
            key_insights=insights,
            source_url=source_url,
            platform=platform,
            created_at=datetime.utcnow(),
        )

    def _segment_content(self, content: str) -> List[str]:
        """Split content into segments (e.g., by paragraphs or code blocks)."""
        # Simple heuristic: split by double newlines or code blocks
        segments = re.split(r"\n\s*\n|```[\s\S]*?```", content)
        return [s.strip() for s in segments if s.strip()]

    async def _process_segment(
        self,
        segment: str,
        platform: str,
        source_url: str,
        conversation_id: str,
        project: Optional[str],
        tags: Optional[List[str]],
    ) -> Insight:
        """Parse and classify a single segment."""
        # Heuristics for feature detection
        features = {
            "is_code": bool(re.search(r"```|\b(function|class|SELECT)\b", segment)),
            "contains_steps": bool(re.match(r"^\d+\.", segment, re.MULTILINE)),
            "contains_problem": any(
                kw in segment.lower() for kw in ["problem", "error", "issue"]
            ),
        }

        # Classify segment
        category = await self._classify_segment(segment, features)

        # Parse based on category
        parsed_data = await self._parse_segment(segment, category)

        # Infer metadata if not provided
        inferred_metadata = await self._infer_metadata(segment, project, tags)
        project = project or inferred_metadata.get("project")
        tags = tags or inferred_metadata.get("tags")
        conversation_title = inferred_metadata.get(
            "conversation_title", "Untitled Chat"
        )

        return Insight(
            id=str(uuid4()),
            type=category,
            content=parsed_data.get("content"),
            synthesis=parsed_data.get("synthesis"),
            problem=parsed_data.get("problem"),
            solution=parsed_data.get("solution"),
            context=parsed_data.get("context"),
            title=parsed_data.get("title"),
            steps=parsed_data.get("steps"),
            tools=parsed_data.get("tools"),
            language=parsed_data.get("language"),
            concepts=parsed_data.get("concepts"),
            tags=tags,
            project=project,
            conversation_id=conversation_id,
            conversation_title=conversation_title,
            source_url=source_url,
            platform=platform,
            created_at=datetime.utcnow(),
        )

    async def _classify_segment(self, text: str, features: Dict[str, Any]) -> str:
        """Classify a segment using Claude."""
        prompt = f"""Classify this text into one category:
        1. CODE - Contains code, commands, or technical artifacts
        2. KNOWLEDGE - Explains concepts, insights, or theoretical knowledge
        3. SOLUTION - Describes a specific problem and its fix or workaround
        4. GUIDE - Step-by-step workflow or repeatable process
        
        Text: "{text}"
        Features: {features}
        Category:"""

        message = self.client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}],
        )
        category = message.content[0].text.strip().lower()
        return category

    async def _parse_segment(self, text: str, category: str) -> Dict[str, Any]:
        """Parse segment based on its category."""
        prompt = f"""Extract structured information based on the category:
        - For CODE: Identify the programming language and provide a summary.
        - For KNOWLEDGE: Synthesize a summary and list key concepts.
        - For SOLUTION: Extract problem, solution, and context.
        - For GUIDE: Extract title, steps, and tools.
        
        Category: {category}
        Text: "{text}"
        
        Return in JSON format:
        ```json
        {{
            "content": "...",  // For code
            "language": "...", // For code
            "synthesis": "...", // For knowledge
            "concepts": ["...", "..."], // For knowledge
            "problem": "...",  // For solution
            "solution": "...", // For solution
            "context": "...",  // For solution
            "title": "...",    // For guide
            "steps": ["...", "..."], // For guide
            "tools": ["...", "..."]  // For guide
        }}
        ```"""

        message = self.client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract JSON from response (Claude might wrap it in markdown)
        response_text = message.content[0].text
        try:
            # Try to find JSON in the response
            json_match = re.search(
                r"```json\s*(\{.*?\})\s*```", response_text, re.DOTALL
            )
            if json_match:
                return json.loads(json_match.group(1))
            else:
                # If no markdown wrapper, try parsing directly
                return json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback to empty dict if JSON parsing fails
            return {}

    async def _infer_metadata(
        self, text: str, project: Optional[str], tags: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Infer project, tags, and conversation title if not provided."""
        prompt = f"""Analyze this text and suggest:
        - A project name (e.g., "React App", max 60 chars)
        - Tags (e.g., ["react", "hooks"])
        - A conversation title (e.g., "React Debugging Session", max 60 chars)
        
        Text: "{text}"
        
        Return in JSON format:
        ```json
        {{
            "project": "...",
            "tags": ["...", "..."],
            "conversation_title": "..."
        }}
        ```"""

        message = self.client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text
        try:
            json_match = re.search(
                r"```json\s*(\{.*?\})\s*```", response_text, re.DOTALL
            )
            if json_match:
                return json.loads(json_match.group(1))
            else:
                return json.loads(response_text)
        except json.JSONDecodeError:
            return {
                "project": "General",
                "tags": [],
                "conversation_title": "Chat Session",
            }

    async def _generate_chat_metadata(self, chat_content: str) -> tuple:
        """Generate high-level chat title and summary."""
        prompt = f"""Analyze this AI conversation and extract:
        - A clear, descriptive title (max 60 chars)
        - A brief summary (2-3 sentences)
        
        Chat content: "{chat_content}"
        
        Return in JSON format:
        ```json
        {{
            "title": "...",
            "summary": "..."
        }}
        ```"""

        message = self.client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text
        try:
            json_match = re.search(
                r"```json\s*(\{.*?\})\s*```", response_text, re.DOTALL
            )
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                result = json.loads(response_text)
            return result["title"], result["summary"]
        except json.JSONDecodeError:
            return "Chat Session", "AI conversation analysis"
