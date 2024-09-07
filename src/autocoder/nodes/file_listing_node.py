import os
import fnmatch
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class FileListingNode:
    def __init__(self, project_root: str, claude_api: Optional[object] = None):
        self.project_root = project_root
        self.claude_api = claude_api
        self.default_exclusions = [
            '.git', '__pycache__', '*.pyc', '*.pyo', '*.pyd',
            '.venv', 'node_modules', 'vendor', '*.log', '*.db',
            '*.sqlite', '*.sqlite3', '*.egg-info', 'build', 'dist'
        ]
        logger.debug(f"FileListingNode initialized with project_root: {project_root}")

    def process(self, state: Dict) -> Dict:
        logger.info("Starting file listing process")
        if not self.files_exist():
            logger.info("Project files or excluded files don't exist. Generating with Claude.")
            if not self.claude_api:
                logger.error("Claude API not available. Cannot generate file lists.")
                return state

            all_files = self.list_all_files()
            generated_lists = self.generate_lists_with_llm(all_files)
        else:
            logger.info("Reading existing file lists")
            generated_lists = {
                "project_files": self.read_file_list("project_files"),
                "excluded_files": self.read_file_list("excluded_files")
            }

        approved_lists = self.get_user_approval(generated_lists)
        self.save_file_lists(approved_lists['project_files'], approved_lists['excluded_files'])

        state['project_files'] = approved_lists['project_files']
        state['excluded_files'] = approved_lists['excluded_files']
        logger.info("File listing process completed")
        return state

    def files_exist(self) -> bool:
        autocoder_dir = os.path.join(self.project_root, '.autocoder')
        project_files_path = os.path.join(autocoder_dir, 'project_files')
        excluded_files_path = os.path.join(autocoder_dir, 'excluded_files')
        exists = os.path.exists(project_files_path) and os.path.exists(excluded_files_path)
        logger.debug(f"Checking if files exist: {exists}")
        return exists

    def list_all_files(self) -> List[str]:
        all_files = []
        for root, dirs, files in os.walk(self.project_root):
            for file in files:
                all_files.append(os.path.relpath(os.path.join(root, file), self.project_root))
        return all_files

    def generate_lists_with_llm(self, all_files: List[str]) -> Dict[str, List[str]]:
        prompt = f"""
        Given the following list of all files in the project directory:

        {', '.join(all_files)}

        Please categorize these files into two lists:
        1. Project Files: Files that are part of the project's source code, configuration, or documentation.
        2. Excluded Files: Files that should be excluded from the project context, such as build artifacts, cache files, or third-party dependencies.

        Provide your response in the following format:

        Project Files:
        - [List of project files, one per line]

        Excluded Files:
        - [List of excluded files, one per line]

        Consider common development patterns and best practices when making your categorization.
        """

        response = self.claude_api.generate_response(prompt)

        # Parse the response
        project_files = []
        excluded_files = []
        current_list = None

        for line in response.split('\n'):
            line = line.strip()
            if line == "Project Files:":
                current_list = project_files
            elif line == "Excluded Files:":
                current_list = excluded_files
            elif line.startswith("- ") and current_list is not None:
                current_list.append(line[2:])

        return {
            "project_files": project_files,
            "excluded_files": excluded_files
        }

    def read_file_list(self, list_name: str) -> List[str]:
        file_path = os.path.join(self.project_root, '.autocoder', list_name)
        with open(file_path, 'r') as f:
            return [line.strip() for line in f if line.strip()]

    def save_file_lists(self, project_files: List[str], excluded_files: List[str]):
        autocoder_dir = os.path.join(self.project_root, '.autocoder')
        os.makedirs(autocoder_dir, exist_ok=True)

        with open(os.path.join(autocoder_dir, 'project_files'), 'w') as f:
            f.write('\n'.join(project_files))

        with open(os.path.join(autocoder_dir, 'excluded_files'), 'w') as f:
            f.write('\n'.join(excluded_files))

    def get_user_approval(self, file_lists: Dict[str, List[str]]) -> Dict[str, List[str]]:
        while True:
            print("\nProject Files:")
            for file in file_lists['project_files']:
                print(f"  {file}")

            print("\nExcluded Files:")
            for file in file_lists['excluded_files']:
                print(f"  {file}")

            approval = input("\nDo you approve these file lists? (yes/no): ").lower()

            if approval == 'yes':
                return file_lists
            elif approval == 'no':
                print(
                    "Please provide your changes in natural language. Describe which files should be moved between lists.")
                changes = input("Your changes: ")
                updated_lists = self.update_lists_with_llm(file_lists, changes)
                file_lists = updated_lists
            else:
                print("Invalid input. Please enter 'yes' or 'no'.")

    def update_lists_with_llm(self, current_lists: Dict[str, List[str]], user_changes: str) -> Dict[str, List[str]]:
        prompt = f"""
        Current file categorization:

        Project Files:
        {', '.join(current_lists['project_files'])}

        Excluded Files:
        {', '.join(current_lists['excluded_files'])}

        User requested changes:
        {user_changes}

        Please update the file lists based on the user's request. Provide your response in the following format:

        Project Files:
        - [Updated list of project files, one per line]

        Excluded Files:
        - [Updated list of excluded files, one per line]
        """

        response = self.claude_api.generate_response(prompt)

        # Parse the response
        project_files = []
        excluded_files = []
        current_list = None

        for line in response.split('\n'):
            line = line.strip()
            if line == "Project Files:":
                current_list = project_files
            elif line == "Excluded Files:":
                current_list = excluded_files
            elif line.startswith("- ") and current_list is not None:
                current_list.append(line[2:])

        return {
            "project_files": project_files,
            "excluded_files": excluded_files
        }


def file_listing_node(state: Dict) -> Dict:
    logger.info("Executing file_listing_node")
    file_lister = FileListingNode(state['project_root'], state.get('claude_api'))
    return file_lister.process(state)
