# src/autocoder/tools/project_analyzer.py

import os
import logging
from pathlib import Path
import fnmatch

logger = logging.getLogger(__name__)


class ProjectAnalyzer:
    def __init__(self, file_manager):
        self.file_manager = file_manager

    def analyze_project(self):
        current_dir = Path.cwd()
        logger.debug(f"ProjectAnalyzer: Analyzing project in directory: {current_dir}")

        if not self._is_project_root(current_dir):
            logger.error("Not in a project root directory. Please navigate to a project root and try again.")
            return None

        project_files = self._get_project_files(current_dir)
        logger.debug(f"Found {len(project_files)} project files")

        project_structure = self._build_project_structure(project_files)
        logger.debug("Built project structure")

        file_contents = self._get_file_contents(project_files)
        logger.debug(f"Read contents of {len(file_contents)} files")

        return {
            "root_directory": str(current_dir),
            "file_list": project_files,
            "project_structure": project_structure,
            "file_contents": file_contents
        }

    def _is_project_root(self, directory):
        indicators = [
            'package.json', 'Cargo.toml', 'pom.xml', 'build.gradle', 'Gemfile',
            'requirements.txt', 'setup.py', 'pyproject.toml', 'composer.json',
            'Makefile', '.git'
        ]
        is_root = any((directory / ind).exists() for ind in indicators)
        logger.debug(f"Is project root: {is_root}")
        return is_root

    def _get_project_files(self, directory):
        project_files = []
        exclude_patterns = [
            '.git', '.svn', '.hg', 'node_modules', 'venv', '.venv', 'vendor',
            '.idea', '.vscode', '*.pyc', '*.pyo', '*.pyd', '*.class',
            '*.o', '*.so', '*.dylib', '*.log', '*.sqlite', '*.db',
            '*~', '.DS_Store',
        ]

        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if not any(fnmatch.fnmatch(d, pat) for pat in exclude_patterns)]
            for file in files:
                if not any(fnmatch.fnmatch(file, pat) for pat in exclude_patterns):
                    full_path = Path(root) / file
                    project_files.append(str(full_path.relative_to(directory)))

        logger.debug(f"Found {len(project_files)} project files")
        return sorted(project_files)

    def _build_project_structure(self, file_list):
        structure = {}
        for file_path in file_list:
            parts = file_path.split(os.sep)
            current = structure
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = None
        return structure

    def _get_file_contents(self, file_list):
        contents = {}
        for file_path in file_list:
            content = self.file_manager.read_file(file_path)
            if content:
                contents[file_path] = content
            else:
                logger.warning(f"Could not read content of {file_path}")
        return contents
