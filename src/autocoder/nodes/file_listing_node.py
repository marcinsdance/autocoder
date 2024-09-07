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
            '*.sqlite', '*.sqlite3', '*.egg-info', 'build', 'dist',
            '*.tfstate', '*.tfstate.*', '.terraform', '*.lock.hcl'
        ]
        logger.debug(f"FileListingNode initialized with project_root: {project_root}")

    def process(self, state: Dict) -> Dict:
        logger.info("Starting file listing process")
        all_files = self.list_all_files()

        if self.claude_api:
            logger.info("Using Claude API for file list generation.")
            generated_lists = self.generate_lists_with_llm(all_files)
        else:
            logger.warning("Claude API not available. Falling back to default exclusions.")
            generated_lists = self.categorize_files_with_defaults(all_files)

        approved_lists = self.get_user_approval(generated_lists)
        self.save_file_lists(approved_lists['project_files'], approved_lists['excluded_files'])

        state['project_files'] = approved_lists['project_files']
        state['excluded_files'] = approved_lists['excluded_files']
        logger.info("File listing process completed")
        return state

    def list_all_files(self) -> List[str]:
        all_files = []
        for root, _, files in os.walk(self.project_root):
            for file in files:
                all_files.append(os.path.relpath(os.path.join(root, file), self.project_root))
        return all_files

    def generate_lists_with_llm(self, all_files: List[str]) -> Dict[str, List[str]]:
        prompt = f"""
        You are an expert in software development and project organization. Given the following list of files in a project directory, categorize them into two lists:
        1. Project Files: Files that are part of the project's source code, configuration, or documentation.
        2. Excluded Files: Files that should be excluded from the project context, such as build artifacts, cache files, third-party dependencies, or automatically generated files.

        Here's the list of all files in the project directory:

        {', '.join(all_files)}

        Consider the following when making your categorization:
        - Common development patterns and best practices
        - Files that are typically version controlled vs. those that are not
        - Configuration files that are important for the project
        - Automatically generated files or build artifacts
        - Backup files or temporary files
        - Dependencies or third-party libraries

        Provide your response in the following format:

        Project Files:
        - [List of project files, one per line]

        Excluded Files:
        - [List of excluded files, one per line]

        Be sure to categorize ALL files from the provided list.
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

    def categorize_files_with_defaults(self, all_files: List[str]) -> Dict[str, List[str]]:
        project_files = []
        excluded_files = []

        for file in all_files:
            if any(fnmatch.fnmatch(file, pattern) for pattern in self.default_exclusions):
                excluded_files.append(file)
            else:
                project_files.append(file)

        return {
            "project_files": project_files,
            "excluded_files": excluded_files
        }

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
                if self.claude_api:
                    print(
                        "Please provide your changes in natural language. Describe which files should be moved between lists.")
                    changes = input("Your changes: ")
                    file_lists = self.update_lists_with_llm(file_lists, changes)
                else:
                    print("Manual update mode:")
                    file_lists = self.manual_file_listing()
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

    def manual_file_listing(self) -> Dict[str, List[str]]:
        all_files = self.list_all_files()
        project_files = []
        excluded_files = []

        print("Manual file listing process:")
        print("For each file, enter 'p' to include it in project files, 'e' to exclude it, or 'q' to finish.")

        for file in all_files:
            while True:
                choice = input(f"{file} (p/e/q): ").lower()
                if choice == 'p':
                    project_files.append(file)
                    break
                elif choice == 'e':
                    excluded_files.append(file)
                    break
                elif choice == 'q':
                    return {"project_files": project_files, "excluded_files": excluded_files}
                else:
                    print("Invalid input. Please enter 'p', 'e', or 'q'.")

        return {"project_files": project_files, "excluded_files": excluded_files}

    def save_file_lists(self, project_files: List[str], excluded_files: List[str]):
        autocoder_dir = os.path.join(self.project_root, '.autocoder')
        os.makedirs(autocoder_dir, exist_ok=True)

        with open(os.path.join(autocoder_dir, 'project_files'), 'w') as f:
            f.write('\n'.join(project_files))

        with open(os.path.join(autocoder_dir, 'excluded_files'), 'w') as f:
            f.write('\n'.join(excluded_files))
