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
        
        all_files = self.list_all_files()
        generated_lists = self.generate_lists_with_llm(all_files)
        
        approved_lists = self.get_user_approval(generated_lists)
        
        if approved_lists:
            self.save_file_lists(approved_lists['project_files'], approved_lists['excluded_files'])
            state['project_files'] = approved_lists['project_files']
            state['excluded_files'] = approved_lists['excluded_files']
            logger.info("File listing process completed successfully")
        else:
            logger.error("User did not approve file lists. Process aborted.")
            return self._update_state_with_error(state, "User did not approve file lists")

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

    def get_user_approval(self, file_lists: Dict[str, List[str]]) -> Dict[str, List[str]] | None:
        while True:
            print("\nProject Files:")
            for file in file_lists['project_files']:
                print(f"  {file}")

            print("\nExcluded Files:")
            for file in file_lists['excluded_files']:
                print(f"  {file}")

            approval = input("\nDo you approve these file lists? (yes/no/quit): ").lower()

            if approval == 'yes':
                return file_lists
            elif approval == 'no':
                print("Please describe the changes you want to make:")
                changes = input("Your changes: ")
                file_lists = self.update_lists_with_llm(file_lists, changes)
            elif approval == 'quit':
                print("Process aborted by user.")
                return None
            else:
                print("Invalid input. Please enter 'yes', 'no', or 'quit'.")

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
