import os
import fnmatch
from typing import List, Dict


class FileListingNode:
    def __init__(self, project_root: str, claude_api):
        self.project_root = project_root
        self.claude_api = claude_api
        self.default_exclusions = [
            '.git', '__pycache__', '*.pyc', '*.pyo', '*.pyd',
            '.venv', 'node_modules', 'vendor', '*.log', '*.db',
            '*.sqlite', '*.sqlite3', '*.egg-info', 'build', 'dist'
        ]

    def process(self, state: Dict) -> Dict:
        if not self.files_exist():
            user_choice = self.prompt_user_for_generation()
            if user_choice.lower() != 'y':
                return state  # Exit if user doesn't want to generate files

        project_files = self.list_project_files()
        excluded_files = self.read_excluded_files()

        refined_lists = self.refine_with_llm(project_files, excluded_files)
        approved_lists = self.get_user_approval(refined_lists)

        self.save_file_lists(approved_lists['project_files'], approved_lists['excluded_files'])

        state['project_files'] = approved_lists['project_files']
        state['excluded_files'] = approved_lists['excluded_files']
        return state

    def files_exist(self) -> bool:
        autocoder_dir = os.path.join(self.project_root, '.autocoder')
        project_files_path = os.path.join(autocoder_dir, 'project_files')
        excluded_files_path = os.path.join(autocoder_dir, 'excluded_files')
        return os.path.exists(project_files_path) and os.path.exists(excluded_files_path)

    def prompt_user_for_generation(self) -> str:
        print("The 'project_files' and 'excluded_files' lists don't exist.")
        return input("Do you want to generate them now? (y/n): ")

    def list_project_files(self) -> List[str]:
        project_files = []
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if not self.is_excluded(d)]
            for file in files:
                if not self.is_excluded(file):
                    project_files.append(os.path.relpath(os.path.join(root, file), self.project_root))
        return project_files

    def is_excluded(self, path: str) -> bool:
        return any(fnmatch.fnmatch(path, pattern) for pattern in self.default_exclusions)

    def read_excluded_files(self) -> List[str]:
        excluded_file_path = os.path.join(self.project_root, '.autocoder', 'excluded_files')
        if os.path.exists(excluded_file_path):
            with open(excluded_file_path, 'r') as f:
                return [line.strip() for line in f if line.strip()]
        return []

    def save_file_lists(self, project_files: List[str], excluded_files: List[str]):
        autocoder_dir = os.path.join(self.project_root, '.autocoder')
        os.makedirs(autocoder_dir, exist_ok=True)

        with open(os.path.join(autocoder_dir, 'project_files'), 'w') as f:
            f.write('\n'.join(project_files))

        with open(os.path.join(autocoder_dir, 'excluded_files'), 'w') as f:
            f.write('\n'.join(excluded_files))

    def refine_with_llm(self, project_files: List[str], excluded_files: List[str]) -> Dict[str, List[str]]:
        prompt = f"""
        Given the following lists of project files and excluded files, please suggest any changes to improve the categorization:

        Project Files:
        {', '.join(project_files)}

        Excluded Files:
        {', '.join(excluded_files)}

        Please provide your suggestions in the following format:
        Project Files to Add: [file1, file2, ...]
        Project Files to Remove: [file1, file2, ...]
        Excluded Files to Add: [file1, file2, ...]
        Excluded Files to Remove: [file1, file2, ...]

        If no changes are needed, please state "No changes needed."
        """

        response = self.claude_api.generate_response(prompt)

        if "No changes needed" in response:
            return {"project_files": project_files, "excluded_files": excluded_files}

        # Parse the response
        lines = response.strip().split('\n')
        changes = {}
        for line in lines:
            if ':' in line:
                key, value = line.split(':')
                changes[key.strip()] = eval(value.strip())  # Use eval to convert string to list

        # Apply changes
        new_project_files = set(project_files) - set(changes.get('Project Files to Remove', []))
        new_project_files.update(changes.get('Project Files to Add', []))

        new_excluded_files = set(excluded_files) - set(changes.get('Excluded Files to Remove', []))
        new_excluded_files.update(changes.get('Excluded Files to Add', []))

        return {
            "project_files": list(new_project_files),
            "excluded_files": list(new_excluded_files)
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
                project_files = input("Enter comma-separated list of project files to keep: ").split(',')
                excluded_files = input("Enter comma-separated list of files to exclude: ").split(',')
                file_lists['project_files'] = [f.strip() for f in project_files if f.strip()]
                file_lists['excluded_files'] = [f.strip() for f in excluded_files if f.strip()]
            else:
                print("Invalid input. Please enter 'yes' or 'no'.")


# This function will be used as the actual node in the graph
def file_listing_node(state: Dict) -> Dict:
    file_lister = FileListingNode(state['project_root'], state['claude_api'])
    return file_lister.process(state)
