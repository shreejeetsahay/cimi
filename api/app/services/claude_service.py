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
                model="claude-3-5-sonnet-20241022",
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
        udf_tags = input_data.get("tags", [])  # Added default empty list
        verbose = input_data.get("verbose", False)  # Add verbose flag
        highlights_text = "\n".join(f"- {h}" for h in highlights)

        prompt = f"""Extract and structure the key information from this content. Emphasize highlighted points.

CONTENT: {chat_content}
HIGHLIGHTS (PRIORITY): {highlights_text}

Instructions: Create a structured summary with markdown formatting. Present information directly without conversational references.

Return a single-line JSON object with no line breaks:
{{"title": "Concise descriptive title", "synthesis": "2-3 sentence high-level summary", "recap": "Well-structured markdown content with headers, bullets, and bold formatting. Use \\n for line breaks.", "suggested_project": "Most appropriate category (e.g. Current Events, Web Development, Team Planning, Personal Learning, Research, Work Discussion)", "suggested_tags": ["3-5 relevant topic tags based on key themes and subjects discussed"]}}

IMPORTANT: Return only valid JSON on a single line. Use \\n for line breaks within strings."""

        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, self._make_sync_api_call, prompt
            )

            print(f"Raw API response: {response}")  # Debug logging

            # Clean and parse response
            response = response.strip()

            # First check for code blocks
            json_match = re.search(
                r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL
            )
            if json_match:
                response = json_match.group(1)

            # Clean and parse response
            response = response.strip()
            json_match = re.search(
                r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL
            )
            if json_match:
                response = json_match.group(1)

            # Try to parse as JSON directly
            try:
                parsed_response = json.loads(response)
            except json.JSONDecodeError as e:
                # Try cleaning the response more aggressively
                try:
                    # Remove extra whitespace and normalize the JSON
                    # Replace literal newlines inside string values with \\n
                    cleaned_response = re.sub(
                        r'"\s*\n\s*"', '""', response
                    )  # Remove empty lines
                    cleaned_response = re.sub(
                        r'(\w+)"\s*\n\s*,', r'\1",', cleaned_response
                    )  # Fix trailing commas
                    cleaned_response = re.sub(
                        r",\s*\n\s*}", "\n}", cleaned_response
                    )  # Fix closing braces

                    parsed_response = json.loads(cleaned_response)
                except json.JSONDecodeError:
                    # Final fallback - manually extract the values
                    print("Attempting manual extraction...")
                    title = re.search(r'"title":\s*"([^"]*)"', response)
                    synthesis = re.search(r'"synthesis":\s*"([^"]*)"', response)
                    project = re.search(r'"suggested_project":\s*"([^"]*)"', response)

                    # Extract recap content between quotes
                    recap_match = re.search(
                        r'"recap":\s*"(.*?)",\s*"suggested_project"',
                        response,
                        re.DOTALL,
                    )
                    recap_content = (
                        recap_match.group(1) if recap_match else "Unable to parse recap"
                    )

                    # Extract tags array
                    tags_match = re.search(
                        r'"suggested_tags":\s*\[(.*?)\]', response, re.DOTALL
                    )
                    if tags_match:
                        tags_str = tags_match.group(1)
                        tags = [
                            tag.strip().strip('"')
                            for tag in tags_str.split(",")
                            if tag.strip()
                        ]
                    else:
                        tags = []

                    parsed_response = {
                        "title": title.group(1) if title else "Chat Summary",
                        "synthesis": (
                            synthesis.group(1)
                            if synthesis
                            else "Error parsing synthesis"
                        ),
                        "recap": recap_content.replace("\\n", "\n"),
                        "suggested_project": project.group(1) if project else "General",
                        "suggested_tags": tags,
                    }

            # Fix: Extract suggested_tags from parsed_response and ensure type safety
            suggested_tags = parsed_response.get("suggested_tags", [])

            # Debug logging to identify the issue
            print(f"udf_tags type: {type(udf_tags)}, value: {udf_tags}")
            print(
                f"suggested_tags type: {type(suggested_tags)}, value: {suggested_tags}"
            )

            # Ensure both are lists before concatenation
            if not isinstance(udf_tags, list):
                print(
                    f"Warning: udf_tags is not a list, converting from {type(udf_tags)}"
                )
                udf_tags = (
                    []
                    if udf_tags is None
                    else list(udf_tags) if hasattr(udf_tags, "__iter__") else []
                )

            if not isinstance(suggested_tags, list):
                print(
                    f"Warning: suggested_tags is not a list, converting from {type(suggested_tags)}"
                )
                suggested_tags = (
                    []
                    if suggested_tags is None
                    else (
                        list(suggested_tags)
                        if hasattr(suggested_tags, "__iter__")
                        else []
                    )
                )

            combined_tags = udf_tags + suggested_tags

            return ChatSummary(
                id=str(uuid4()),
                title=parsed_response.get("title", "Chat Summary"),
                synthesis=parsed_response.get("synthesis", ""),
                recap=parsed_response.get("recap", ""),
                project_name=parsed_response.get("suggested_project", "General"),
                tags=list(set(combined_tags)),  # Fixed line with type safety
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
