import os
import logging
from typing import List, Dict, Tuple, Set

logger = logging.getLogger(__name__)


class FileListingNode:
    def __init__(self, project_root: str, claude_api):
        self.project_root = project_root
        self.claude_api = claude_api
        logger.debug(f"FileListingNode initialized with project_root: {project_root}")
        self.common_excludes = {
            '__pycache__', '*.pyc', '*.pyo', '*.pyd',
            '.git', '.idea', '.vscode', '*.egg-info',
            'build', 'dist', '.tox', '.pytest_cache',
            '*.log', '*.sqlite3', '*.db', '*.swp',
            '.DS_Store', 'Thumbs.db'
        }
        self.auto_excluded_items: Set[str] = set()

    def process(self, state: Dict) -> Dict:
        logger.info("Starting file listing process")

        root_items = self.list_root_items()
        filtered_items = self.filter_common_excludes(root_items)
        generated_lists = self.generate_lists_with_llm(filtered_items)

        approved_lists = self.get_user_approval(generated_lists)

        if approved_lists:
            project_items = self.expand_approved_items(approved_lists['project_items'])
            excluded_items = set(approved_lists['excluded_items']) | self.auto_excluded_items

            self.save_item_lists(project_items, list(excluded_items))
            state['project_items'] = project_items
            state['excluded_items'] = list(excluded_items)
            logger.info("File and directory listing process completed successfully")
        else:
            logger.error("User did not approve item lists. Process aborted.")
            return self._update_state_with_error(state, "User did not approve item lists")

        return state

    def list_root_items(self) -> List[Tuple[str, str]]:
        root_items = []
        for item in os.listdir(self.project_root):
            full_path = os.path.join(self.project_root, item)
            item_type = 'directory' if os.path.isdir(full_path) else 'file'
            root_items.append((item, item_type))
        return root_items

    def filter_common_excludes(self, items: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        filtered_items = []
        for item, item_type in items:
            if not self.should_exclude(item):
                filtered_items.append((item, item_type))
            else:
                self.auto_excluded_items.add(item)
        return filtered_items

    def should_exclude(self, item: str) -> bool:
        return any(self.match_pattern(item, pattern) for pattern in self.common_excludes)

    def match_pattern(self, item: str, pattern: str) -> bool:
        if pattern.startswith('*'):
            return item.endswith(pattern[1:])
        return item == pattern

    def expand_approved_items(self, approved_items: List[str]) -> List[str]:
        expanded_items = []
        for item in approved_items:
            full_path = os.path.join(self.project_root, item)
            if os.path.isdir(full_path):
                for root, dirs, files in os.walk(full_path):
                    rel_root = os.path.relpath(root, self.project_root)
                    dirs[:] = [d for d in dirs if not self.should_exclude(d)]
                    for file in files:
                        if not self.should_exclude(file):
                            rel_path = os.path.join(rel_root, file)
                            expanded_items.append(rel_path)
                        else:
                            self.auto_excluded_items.add(os.path.join(rel_root, file))
                expanded_items.append(item)  # Include the directory itself
            else:
                expanded_items.append(item)  # It's a file, just add it
        return sorted(set(expanded_items))  # Remove duplicates and sort

    def generate_lists_with_llm(self, root_items: List[Tuple[str, str]]) -> Dict[str, List[str]]:
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
            return {"project_items": [], "excluded_items": []}

        # Parse the response
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

    def get_user_approval(self, item_lists: Dict[str, List[str]]) -> Dict[str, List[str]] | None:
        while True:
            print("\nProject Items:")
            for item in item_lists['project_items']:
                print(f"  {item}")

            print("\nExcluded Items:")
            for item in item_lists['excluded_items']:
                print(f"  {item}")

            print("\nAutomatically Excluded Items:")
            for item in sorted(self.auto_excluded_items):
                print(f"  {item}")

            approval = input("\nDo you approve these item lists? (yes/no/quit): ").lower()

            if approval == 'yes':
                return item_lists
            elif approval == 'no':
                print("Please describe the changes you want to make:")
                changes = input("Your changes: ")
                item_lists = self.update_lists_with_llm(item_lists, changes)
            elif approval == 'quit':
                print("Process aborted by user.")
                return None
            else:
                print("Invalid input. Please enter 'yes', 'no', or 'quit'.")

    def update_lists_with_llm(self, current_lists: Dict[str, List[str]], user_changes: str) -> Dict[str, List[str]]:
        system_prompt = """You are an expert in software development and project organization. Your task is to update the categorization of files and directories based on user feedback."""

        user_prompt = f"""Current root item categorization:

        Project Items:
        {', '.join(current_lists['project_items'])}

        Excluded Items:
        {', '.join(current_lists['excluded_items'])}

        Automatically Excluded Items:
        {', '.join(sorted(self.auto_excluded_items))}

        User requested changes:
        {user_changes}

        Please update the root item lists based on the user's request. Provide your response in the following format:

        Project Items:
        - [Updated list of project files and directories, one per line]

        Excluded Items:
        - [Updated list of excluded files and directories, one per line]"""

        prompt = self.claude_api.format_prompt(system_prompt, user_prompt)
        response = self.claude_api.generate_response(prompt)

        if response is None:
            logger.error("Failed to generate response from Claude API")
            return current_lists

        # Parse the response
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

    def save_item_lists(self, project_items: List[str], excluded_items: List[str]):
        autocoder_dir = os.path.join(self.project_root, '.autocoder')
        os.makedirs(autocoder_dir, exist_ok=True)

        with open(os.path.join(autocoder_dir, 'project_items'), 'w') as f:
            f.write('\n'.join(project_items))

        with open(os.path.join(autocoder_dir, 'excluded_items'), 'w') as f:
            f.write('\n'.join(excluded_items))

    def _update_state_with_error(self, state: Dict, error_message: str) -> Dict:
        state['error'] = error_message
        return state


def file_listing_node(state: Dict) -> Dict:
    logger.info("Executing file_listing_node")
    file_lister = FileListingNode(state['project_root'], state['claude_api'])
    return file_lister.process(state)
