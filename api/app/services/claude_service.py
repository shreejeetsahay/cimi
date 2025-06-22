import anthropic
import os
import re
import json
import asyncio
from typing import Dict, Any
from datetime import datetime
from uuid import uuid4
from app.models.chat import ChatSummary


class ClaudeService:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def _make_sync_api_call(self, prompt: str, max_tokens: int = 2000) -> str:
        """Make a synchronous API call to Claude."""
        try:
            message = self.client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text.strip()
        except Exception as e:
            print(f"API call error: {e}")
            raise e  # Re-raise to see the actual error

    async def summarize_chat(self, input_data: Dict[str, Any]) -> ChatSummary:
        """Summarize chat content with emphasis on highlights."""
        chat_content = input_data.get("chat_content", "")
        highlights = input_data.get("highlights", [])
        source_url = input_data.get("source_url", "")
        platform = input_data.get("platform", "")
        udf_tags = input_data.get("tags")
        highlights_text = "\n".join(f"- {h}" for h in highlights)

        prompt = f"""Extract and structure the key information from this content. Emphasize highlighted points.

CONTENT: {chat_content}
HIGHLIGHTS (PRIORITY): {highlights_text}

Instructions: Create a structured summary with markdown formatting. Present information directly without conversational references.

Return JSON:
{{
   "title": "Concise descriptive title",
   "synthesis": "2-3 sentence high-level summary", 
   "recap": "Well-structured markdown content with headers, bullets, and bold formatting. Present information directly without conversational references.",
   "suggested_project": "Most appropriate category (e.g. Current Events, Web Development, Team Planning, Personal Learning, Research, Work Discussion)",
   "suggested_tags": ["3-5 relevant topic tags based on key themes and subjects discussed"]
}}"""

        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, self._make_sync_api_call, prompt
            )

            print(f"Raw API response: {response}")  # Debug logging

            # Clean and parse response
            response = response.strip()
            json_match = re.search(
                r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL
            )
            if json_match:
                response = json_match.group(1)

            # Try to parse as JSON directly if no code blocks found
            try:
                parsed_response = json.loads(response)
            except json.JSONDecodeError:
                # If it's not wrapped in code blocks and not valid JSON, try to extract JSON
                json_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", response)
                if json_match:
                    parsed_response = json.loads(json_match.group(0))
                else:
                    raise ValueError("No valid JSON found in response")

            return ChatSummary(
                id=str(uuid4()),
                title=parsed_response.get("title", "Chat Summary"),
                synthesis=parsed_response.get("synthesis", ""),
                recap=parsed_response.get("recap", ""),
                project_name=parsed_response.get("suggested_project", "General"),
                tags=list(set(udf_tags + parsed_response)),
                source_url=source_url,
                platform=platform,
                created_at=datetime.utcnow(),
            )

        except Exception as e:
            print(f"Error summarizing chat: {e}")
            print(
                f"Raw response that failed: {response if 'response' in locals() else 'No response received'}"
            )
            return ChatSummary(
                id=str(uuid4()),
                title="Chat Summary",
                synthesis="Error processing chat content",
                recap="Unable to generate detailed recap",
                project_name="General",
                tags=[],
                source_url=source_url,
                platform=platform,
                created_at=datetime.utcnow(),
            )
