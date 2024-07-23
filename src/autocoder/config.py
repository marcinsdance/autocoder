import os
from pathlib import Path
from dotenv import load_dotenv


class Config:
    def __init__(self):
        # Load .env file from the user's home directory
        home_dir = str(Path.home())
        env_path = os.path.join(home_dir, '.autocoder.env')
        load_dotenv(env_path)

        # Determine the project directory
        self.project_directory = self._determine_project_directory()

        # Get the API key, preferring ANTHROPIC_API_KEY if both are present
        self.api_key = self._get_api_key()

        if not self.api_key:
            raise ValueError(
                "Neither ANTHROPIC_API_KEY nor CLAUDE_API_KEY is set in the environment variables or .autocoder.env file in your home directory")

    def _determine_project_directory(self):
        # First, use the current working directory
        cwd = os.getcwd()

        # Then, check if PROJECT_DIRECTORY is set in .env
        env_project_dir = os.getenv('PROJECT_DIRECTORY')

        # Prioritize current working directory, fall back to env variable if set
        return cwd if cwd != "/" else (env_project_dir or cwd)

    def _get_api_key(self):
        # Prefer ANTHROPIC_API_KEY, but fall back to CLAUDE_API_KEY if necessary
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        claude_key = os.getenv('CLAUDE_API_KEY')

        return anthropic_key or claude_key

    def get_project_directory(self):
        return self.project_directory

    def get_api_key(self):
        return self.api_key
