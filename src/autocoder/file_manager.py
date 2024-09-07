import os
import fnmatch
from typing import List, Dict

class FileManager:
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.project_files: List[str] = []
        self.excluded_files: List[str] = []

    def read_file(self, file_path: str) -> str:
        with open(os.path.join(self.project_root, file_path), 'r') as file:
            return file.read()

    def write_file(self, file_path: str, content: str):
        with open(os.path.join(self.project_root, file_path), 'w') as file:
            file.write(content)

    def load_file_lists(self):
        autocoder_dir = os.path.join(self.project_root, '.autocoder')
        project_files_path = os.path.join(autocoder_dir, 'project_files')
        excluded_files_path = os.path.join(autocoder_dir, 'excluded_files')

        if os.path.exists(project_files_path):
            with open(project_files_path, 'r') as f:
                self.project_files = [line.strip() for line in f if line.strip()]

        if os.path.exists(excluded_files_path):
            with open(excluded_files_path, 'r') as f:
                self.excluded_files = [line.strip() for line in f if line.strip()]

    def get_file_contents(self) -> Dict[str, str]:
        return {file: self.read_file(file) for file in self.project_files}

    def is_debug_mode(self) -> bool:
        return os.getenv('DEBUG', 'false').lower() == 'true'

    def create_debug_context(self):
        if not self.is_debug_mode():
            return

        debug_context = ""
        for file in self.project_files:
            debug_context += f"#File {file}:\n{self.read_file(file)}\n\n"

        debug_context_path = os.path.join(self.project_root, '.autocoder', 'debug_context.txt')
        self.write_file(debug_context_path, debug_context)

    def get_context(self) -> str:
        if self.is_debug_mode():
            debug_context_path = os.path.join(self.project_root, '.autocoder', 'debug_context.txt')
            return self.read_file(debug_context_path)
        else:
            return "\n\n".join([f"#File {file}:\n{self.read_file(file)}" for file in self.project_files])
