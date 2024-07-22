import os
import glob
import fnmatch

class ManifestProcessor:
    def __init__(self, project_root):
        self.project_root = project_root
        self.exclude_patterns = [
            '.venv', '__pycache__', '*.pyc', '*.pyo', '*.pyd',
            '.git', '.idea', '.vscode', '*.egg-info',
            'build', 'dist', '.tox', '.pytest_cache'
        ]

    def is_excluded(self, path):
        abs_path = os.path.abspath(path)
        path_parts = abs_path.split(os.sep)
        for i in range(len(path_parts)):
            current_path = os.sep.join(path_parts[:i+1])
            if any(fnmatch.fnmatch(os.path.basename(current_path), pattern) for pattern in self.exclude_patterns):
                return True
        return False

    def process_manifest(self, manifest_file='MANIFEST.in'):
        manifest_path = os.path.join(self.project_root, manifest_file)
        if not os.path.exists(manifest_path):
            print(f"Error: {manifest_file} not found in the project root directory.")
            return []

        included_files = set()
        excluded_files = set()

        with open(manifest_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split()
                command = parts[0].lower()
                patterns = parts[1:]

                if command in ('include', 'recursive-include'):
                    self._handle_include(command, patterns, included_files)
                elif command in ('exclude', 'recursive-exclude'):
                    self._handle_exclude(command, patterns, excluded_files)
                elif command == 'global-include':
                    self._handle_global_include(patterns, included_files)
                elif command == 'global-exclude':
                    self._handle_global_exclude(patterns, excluded_files)

        final_files = sorted(included_files - excluded_files)
        return final_files

    def _handle_include(self, command, patterns, included_files):
        for pattern in patterns:
            if command == 'include':
                included_files.update(f for f in glob.glob(os.path.join(self.project_root, pattern)) if not self.is_excluded(f))
            else:  # recursive-include
                for root, _, filenames in os.walk(self.project_root):
                    if not self.is_excluded(root):
                        for filename in fnmatch.filter(filenames, pattern):
                            path = os.path.join(root, filename)
                            if not self.is_excluded(path):
                                included_files.add(path)

    def _handle_exclude(self, command, patterns, excluded_files):
        for pattern in patterns:
            if command == 'exclude':
                excluded_files.update(glob.glob(os.path.join(self.project_root, pattern)))
            else:  # recursive-exclude
                for root, _, filenames in os.walk(self.project_root):
                    for filename in fnmatch.filter(filenames, pattern):
                        excluded_files.add(os.path.join(root, filename))

    def _handle_global_include(self, patterns, included_files):
        for pattern in patterns:
            for root, _, filenames in os.walk(self.project_root):
                if not self.is_excluded(root):
                    included_files.update(
                        os.path.join(root, f) for f in fnmatch.filter(filenames, pattern)
                        if not self.is_excluded(os.path.join(root, f))
                    )

    def _handle_global_exclude(self, patterns, excluded_files):
        for pattern in patterns:
            for root, _, filenames in os.walk(self.project_root):
                excluded_files.update(
                    os.path.join(root, f) for f in fnmatch.filter(filenames, pattern)
                )
