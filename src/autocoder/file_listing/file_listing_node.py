import os
import logging
from pathlib import Path
import pathspec
from typing import Dict, List, Any
from ..claude_api_wrapper import ClaudeAPIWrapper

logger = logging.getLogger(__name__)

class FileListingNode:
    def __init__(self, project_root: str, claude_api: ClaudeAPIWrapper):
        self.project_root = Path(project_root)
        self.claude_api = claude_api

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self.project_root = Path(state['project_root'])
            ignore_spec = self.get_ignore_spec()
            project_files = self.list_project_files(ignore_spec)
            context = self.build_context(project_files)

            return {
                'project_files': project_files,
                'excluded_files': [str(pat) for pat in ignore_spec.patterns],
                'context': context
            }
        except Exception as e:
            logger.error(f"Error in FileListingNode: {str(e)}")
            return {'error': str(e)}

    def get_ignore_spec(self) -> pathspec.PathSpec:
        patterns = []
        gitignore_path = self.project_root / '.gitignore'
        if gitignore_path.exists():
            with gitignore_path.open('r') as f:
                patterns.extend(f.read().splitlines())
            logger.info("Read .gitignore and compiled ignore patterns.")
        else:
            logger.warning(".gitignore file not found.")

        default_ignores = [
            '.git/', '.hg/', '.svn/', '.idea/', '*.egg-info/',
            '__pycache__/', '.DS_Store', '*.pyc', '.venv/',
            'env/', 'build/', 'dist/', 'node_modules/',
            '*.log', '*.tmp',
        ]
        patterns.extend(default_ignores)
        return pathspec.PathSpec.from_lines('gitwildmatch', patterns)

    def list_project_files(self, ignore_spec: pathspec.PathSpec) -> List[str]:
        project_files = []
        for root, dirs, files in os.walk(self.project_root):
            root_path = Path(root)
            rel_root = root_path.relative_to(self.project_root)
            dirs[:] = [d for d in dirs if not ignore_spec.match_file(str(rel_root / d) + '/')]
            for file in files:
                rel_path = rel_root / file
                if not ignore_spec.match_file(str(rel_path)):
                    project_files.append(str(rel_path))
        return project_files

    def build_context(self, project_files: List[str]) -> str:
        context = "Project Files:\n"
        context += "\n".join(project_files)
        context += "\n\nFile Contents:\n"

        for file in project_files[:10]:  # Limit to first 10 files to avoid overwhelming the LLM
            file_path = self.project_root / file
            try:
                with file_path.open('r', encoding='utf-8') as f:
                    content = f.read()
                context += f'\n\n#File {file}:\n{content[:1000]}'  # Limit each file to first 1000 characters
            except Exception as e:
                logger.warning(f"Could not read file {file}: {str(e)}")

        return context
