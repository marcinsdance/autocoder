import os
from pathlib import Path
import logging
import pathspec

logger = logging.getLogger(__name__)

class FileListingNode:
    def __init__(self, project_root, claude_api):
        self.project_root = Path(project_root)
        self.claude_api = claude_api

    def process(self, state):
        try:
            ignore_spec = self.read_gitignore()
            project_files = self.list_project_files(ignore_spec)
            state['project_files'] = project_files
            state['excluded_files'] = [str(pat) for pat in ignore_spec.patterns]
            # Build context
            context = self.build_context(project_files)
            state['context'] = context
            logger.info("Context built successfully.")
            return state
        except Exception as e:
            logger.error(f"Error in FileListingNode: {str(e)}")
            state['error'] = str(e)
            return state

    def read_gitignore(self):
        gitignore_path = self.project_root / '.gitignore'
        if gitignore_path.exists():
            with gitignore_path.open('r') as f:
                gitignore_content = f.read()
            spec = pathspec.PathSpec.from_lines('gitwildmatch', gitignore_content.splitlines())
            logger.info("Read .gitignore and compiled ignore patterns.")
        else:
            logger.warning(".gitignore file not found.")
            spec = pathspec.PathSpec.from_lines('gitwildmatch', [])
        return spec

    def list_project_files(self, ignore_spec):
        project_files = []
        for root, dirs, files in os.walk(self.project_root):
            # Compute relative paths
            root_relative = os.path.relpath(root, self.project_root)
            if root_relative == '.':
                root_relative = ''
            # Exclude directories matching ignore patterns
            dirs[:] = [d for d in dirs if not ignore_spec.match_file(os.path.join(root_relative, d))]
            for file in files:
                rel_path = os.path.join(root_relative, file)
                if not ignore_spec.match_file(rel_path):
                    project_files.append(rel_path)
        logger.info(f"Listed project files: {len(project_files)} files found.")
        return project_files

    def build_context(self, project_files):
        context = ''
        for file in project_files:
            file_path = self.project_root / file
            try:
                with file_path.open('r', encoding='utf-8') as f:
                    content = f.read()
                context += f'#File {file}:\n{content}\n\n'
            except Exception as e:
                logger.warning(f"Could not read file {file}: {str(e)}")
        logger.info("Built context from project files.")
        return context
