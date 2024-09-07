import os
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class FileListingNode:
    def __init__(self, project_root: str, claude_api):
        self.project_root = project_root
        self.claude_api = claude_api
        logger.debug(f"FileListingNode initialized with project_root: {project_root}")

    def process(self, state: Dict) -> Dict:
        logger.info("Starting file listing process")

        directories = self.list_directories()
        generated_lists = self.generate_lists_with_llm(directories)

        approved_lists = self.get_user_approval(generated_lists)

        if approved_lists:
            expanded_files = self.expand_directories(approved_lists['project_files'])
            self.save_file_lists(expanded_files, approved_lists['excluded_files'])
            state['project_files'] = expanded_files
            state['excluded_files'] = approved_lists['excluded_files']
            logger.info("File listing process completed successfully")
        else:
            logger.error("User did not approve file lists. Process aborted.")
            return self._update_state_with_error(state, "User did not approve file lists")

        return state

    def list_directories(self) -> List[str]:
        directories = []
        for root, dirs, _ in os.walk(self.project_root):
            for dir in dirs:
                rel_path = os.path.relpath(os.path.join(root, dir), self.project_root)
                directories.append(rel_path)
        return directories

    def expand_directories(self, approved_directories: List[str]) -> List[str]:
        expanded_files = []
        for directory in approved_directories:
            for root, _, files in os.walk(os.path.join(self.project_root, directory)):
                for file in files:
                    rel_path = os.path.relpath(os.path.join(root, file), self.project_root)
                    expanded_files.append(rel_path)
        return expanded_files

    def generate_lists_with_llm(self, directories: List[str]) -> Dict[str, List[str]]:
        prompt = f"""
        You are an expert in software development and project organization. Given the following list of directories in a project, categorize them into two lists:
        1. Project Directories: Directories that are likely to contain source code, configuration, or documentation.
        2. Excluded Directories: Directories that should be excluded from the project context, such as build artifacts, cache directories, or third-party dependencies.

        Here's the list of all directories in the project:

        {', '.join(directories)}

        Consider the following when making your categorization:
        - Common development patterns and best practices
        - Directories that typically contain source code or important project files
        - Directories that usually contain build artifacts or generated files
        - Directories for dependencies or third-party libraries

        Provide your response in the following format:

        Project Directories:
        - [List of project directories, one per line]

        Excluded Directories:
        - [List of excluded directories, one per line]

        Be sure to categorize ALL directories from the provided list.
        """

        response = self.claude_api.generate_response(prompt)

        # Parse the response
        project_dirs = []
        excluded_dirs = []
        current_list = None

        for line in response.split('\n'):
            line = line.strip()
            if line == "Project Directories:":
                current_list = project_dirs
            elif line == "Excluded Directories:":
                current_list = excluded_dirs
            elif line.startswith("- ") and current_list is not None:
                current_list.append(line[2:])

        return {
            "project_files": project_dirs,
            "excluded_files": excluded_dirs
        }

    def get_user_approval(self, dir_lists: Dict[str, List[str]]) -> Dict[str, List[str]] | None:
        while True:
            print("\nProject Directories:")
            for dir in dir_lists['project_files']:
                print(f"  {dir}")

            print("\nExcluded Directories:")
            for dir in dir_lists['excluded_files']:
                print(f"  {dir}")

            approval = input("\nDo you approve these directory lists? (yes/no/quit): ").lower()

            if approval == 'yes':
                return dir_lists
            elif approval == 'no':
                print("Please describe the changes you want to make:")
                changes = input("Your changes: ")
                dir_lists = self.update_lists_with_llm(dir_lists, changes)
            elif approval == 'quit':
                print("Process aborted by user.")
                return None
            else:
                print("Invalid input. Please enter 'yes', 'no', or 'quit'.")

    def update_lists_with_llm(self, current_lists: Dict[str, List[str]], user_changes: str) -> Dict[str, List[str]]:
        prompt = f"""
        Current directory categorization:

        Project Directories:
        {', '.join(current_lists['project_files'])}

        Excluded Directories:
        {', '.join(current_lists['excluded_files'])}

        User requested changes:
        {user_changes}

        Please update the directory lists based on the user's request. Provide your response in the following format:

        Project Directories:
        - [Updated list of project directories, one per line]

        Excluded Directories:
        - [Updated list of excluded directories, one per line]
        """

        response = self.claude_api.generate_response(prompt)

        # Parse the response
        project_dirs = []
        excluded_dirs = []
        current_list = None

        for line in response.split('\n'):
            line = line.strip()
            if line == "Project Directories:":
                current_list = project_dirs
            elif line == "Excluded Directories:":
                current_list = excluded_dirs
            elif line.startswith("- ") and current_list is not None:
                current_list.append(line[2:])

        return {
            "project_files": project_dirs,
            "excluded_files": excluded_dirs
        }

    def save_file_lists(self, project_files: List[str], excluded_files: List[str]):
        autocoder_dir = os.path.join(self.project_root, '.autocoder')
        os.makedirs(autocoder_dir, exist_ok=True)

        with open(os.path.join(autocoder_dir, 'project_files'), 'w') as f:
            f.write('\n'.join(project_files))

        with open(os.path.join(autocoder_dir, 'excluded_files'), 'w') as f:
            f.write('\n'.join(excluded_files))

    def _update_state_with_error(self, state: Dict, error_message: str) -> Dict:
        state['error'] = error_message
        return state


def file_listing_node(state: Dict) -> Dict:
    logger.info("Executing file_listing_node")
    file_lister = FileListingNode(state['project_root'], state['claude_api'])
    return file_lister.process(state)
