import os
from dotenv import load_dotenv


class Config:
    def __init__(self):
        # Load .env file from the current working directory
        load_dotenv()

        # Determine the project directory
        self.project_directory = self._determine_project_directory()

        # Get the API key, preferring ANTHROPIC_API_KEY if both are present
        self.api_key = self._get_api_key()

        if not self.api_key:
            raise ValueError(
                "Neither ANTHROPIC_API_KEY nor CLAUDE_API_KEY is set in the environment variables or .env file")

    def _determine_project_directory(self):
        # First, check if PROJECT_DIRECTORY is set in .env
        env_project_dir = os.getenv('PROJECT_DIRECTORY')
        if env_project_dir:
            return env_project_dir

        # If not set in .env, use the current working directory
        return os.getcwd()

    def _get_api_key(self):
        # Prefer ANTHROPIC_API_KEY, but fall back to CLAUDE_API_KEY if necessary
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        claude_key = os.getenv('CLAUDE_API_KEY')

        return anthropic_key or claude_key

    def get_project_directory(self):
        return self.project_directory

    def get_api_key(self):
        return self.api_key
