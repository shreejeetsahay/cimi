# api/app/services/claude_service.py
import anthropic
import os
from typing import List


class ClaudeService:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async def synthesize_chat(self, chat_content: str) -> dict:
        """Use Claude to extract key insights from chat content"""
        prompt = f"""
        Analyze this AI conversation and extract:
        1. A clear, descriptive title (max 60 chars)
        2. A brief summary (2-3 sentences)
        3. Key insights/solutions/frameworks (bullet points)
        
        Chat content:
        {chat_content}
        
        Return in JSON format:
        {{
            "title": "...",
            "summary": "...",
            "key_insights": ["...", "...", "..."]
        }}
        """

        message = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )

        # TODO: Parse JSON response and return structured data
        return {"title": "", "summary": "", "key_insights": []}
