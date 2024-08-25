import os
import fnmatch

class FileManager:
    def __init__(self):
        self.exclude_patterns = [
            '.venv', '__pycache__', '*.pyc', '*.pyo', '*.pyd',
            '.git', '.idea', '.vscode', '*.egg-info',
            'build', 'dist', '.tox', '.pytest_cache'
        ]

    def read_file(self, file_path):
        with open(file_path, 'r') as file:
            return file.read()

    def write_file(self, file_path, content):
        with open(file_path, 'w') as file:
            file.write(content)

    def list_files(self):
        files = []
        for root, _, filenames in os.walk('.'):
            if not self._is_excluded(root):
                for filename in filenames:
                    if not self._is_excluded(filename):
                        files.append(os.path.join(root, filename))
        return files

    def get_file_contents(self):
        files = self.list_files()
        return {file: self.read_file(file) for file in files}

    def _is_excluded(self, path):
        return any(fnmatch.fnmatch(os.path.basename(path), pattern) for pattern in self.exclude_patterns)
