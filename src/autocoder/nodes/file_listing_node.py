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

        root_directories = self.list_root_directories()
        generated_lists = self.generate_lists_with_llm(root_directories)

        approved_lists = self.get_user_approval(generated_lists)

        if approved_lists:
            expanded_dirs = self.expand_approved_directories(approved_lists['project_directories'])
            self.save_directory_lists(expanded_dirs, approved_lists['excluded_directories'])
            state['project_directories'] = expanded_dirs
            state['excluded_directories'] = approved_lists['excluded_directories']
            logger.info("Directory listing process completed successfully")
        else:
            logger.error("User did not approve directory lists. Process aborted.")
            return self._update_state_with_error(state, "User did not approve directory lists")

        return state

    def list_root_directories(self) -> List[str]:
        return [d for d in os.listdir(self.project_root)
                if os.path.isdir(os.path.join(self.project_root, d))]

    def expand_approved_directories(self, approved_directories: List[str]) -> List[str]:
        expanded_dirs = []
        for directory in approved_directories:
            for root, dirs, _ in os.walk(os.path.join(self.project_root, directory)):
                for dir in dirs:
                    rel_path = os.path.relpath(os.path.join(root, dir), self.project_root)
                    expanded_dirs.append(rel_path)
            expanded_dirs.append(directory)  # Include the root directory itself
        return sorted(set(expanded_dirs))  # Remove duplicates and sort

    def generate_lists_with_llm(self, directories: List[str]) -> Dict[str, List[str]]:
        prompt = f"""
        You are an expert in software development and project organization. Given the following list of root-level directories in a project, categorize them into two lists:
        1. Project Directories: Directories that are likely to contain source code, configuration, or documentation.
        2. Excluded Directories: Directories that should be excluded from the project context, such as build artifacts, cache directories, or third-party dependencies.

        Here's the list of all root-level directories in the project:

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
            "project_directories": project_dirs,
            "excluded_directories": excluded_dirs
        }

    def get_user_approval(self, dir_lists: Dict[str, List[str]]) -> Dict[str, List[str]] | None:
        while True:
            print("\nProject Directories:")
            for dir in dir_lists['project_directories']:
                print(f"  {dir}")

            print("\nExcluded Directories:")
            for dir in dir_lists['excluded_directories']:
                print(f"  {dir}")

            approval = input("\nDo you approve these root directory lists? (yes/no/quit): ").lower()

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
        Current root directory categorization:

        Project Directories:
        {', '.join(current_lists['project_directories'])}

        Excluded Directories:
        {', '.join(current_lists['excluded_directories'])}

        User requested changes:
        {user_changes}

        Please update the root directory lists based on the user's request. Provide your response in the following format:

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
            "project_directories": project_dirs,
            "excluded_directories": excluded_dirs
        }

    def save_directory_lists(self, project_directories: List[str], excluded_directories: List[str]):
        autocoder_dir = os.path.join(self.project_root, '.autocoder')
        os.makedirs(autocoder_dir, exist_ok=True)

        with open(os.path.join(autocoder_dir, 'project_directories'), 'w') as f:
            f.write('\n'.join(project_directories))

        with open(os.path.join(autocoder_dir, 'excluded_directories'), 'w') as f:
            f.write('\n'.join(excluded_directories))

    def _update_state_with_error(self, state: Dict, error_message: str) -> Dict:
        state['error'] = error_message
        return state


def file_listing_node(state: Dict) -> Dict:
    logger.info("Executing file_listing_node")
    file_lister = FileListingNode(state['project_root'], state['claude_api'])
    return file_lister.process(state)
