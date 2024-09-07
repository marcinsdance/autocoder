from typing import List, Tuple, Dict
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class LLMCategorizer:
    def __init__(self, claude_api):
        self.claude_api = claude_api

    def generate_lists(self, root_items: List[Tuple[str, str]]) -> dict[str, list[str]] | None:
        system_prompt = """You are an expert in software development and project organization. Your task is to categorize files and directories in a project."""

        user_prompt = f"""Given the following list of root-level items (files and directories) in a project, categorize them into two lists:
        1. Project Items: Files and directories that are likely to contain source code, configuration, or documentation.
        2. Excluded Items: Files and directories that should be excluded from the project context, such as build artifacts, cache files/directories, or third-party dependencies.

        Here's the list of all root-level items in the project:

        {', '.join([f"{item} ({item_type})" for item, item_type in root_items])}

        Consider the following when making your categorization:
        - Common development patterns and best practices
        - Files and directories that typically contain source code or important project files
        - Files and directories that usually contain build artifacts or generated content
        - Dependencies or third-party libraries
        - Configuration files that are important for the project
        - Temporary or backup files

        Provide your response in the following format:

        Project Items:
        - [List of project files and directories, one per line]

        Excluded Items:
        - [List of excluded files and directories, one per line]

        Be sure to categorize ALL items from the provided list."""

        prompt = self.claude_api.format_prompt(system_prompt, user_prompt)
        response = self.claude_api.generate_response(prompt)

        if response is None:
            logger.error("Failed to generate response from Claude API")
            return None

        return self._parse_response(response)

    def _parse_response(self, response: str) -> Dict[str, List[str]]:
        project_items = []
        excluded_items = []
        current_list = None

        for line in response.split('\n'):
            line = line.strip()
            if line == "Project Items:":
                current_list = project_items
            elif line == "Excluded Items:":
                current_list = excluded_items
            elif line.startswith("- ") and current_list is not None:
                current_list.append(line[2:])

        return {
            "project_items": project_items,
            "excluded_items": excluded_items
        }
