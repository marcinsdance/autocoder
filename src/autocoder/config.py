import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        self.api_key = self._get_api_key()

        if not self.api_key:
            raise ValueError(
                "Neither ANTHROPIC_API_KEY nor CLAUDE_API_KEY is set in the environment variables or .env file")

    def _get_api_key(self):
        # Prefer ANTHROPIC_API_KEY, but fall back to CLAUDE_API_KEY if necessary
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        claude_key = os.getenv('CLAUDE_API_KEY')

        return anthropic_key or claude_key

    def get_api_key(self):
        return self.api_key
