import os
import logging
from pathlib import Path
import pathspec
from typing import Dict, List, Any
from ..claude_api_wrapper import ClaudeAPIWrapper
from langchain_core.tools import Tool
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class FileListingArgs(BaseModel):
    project_root: str = Field(..., description="Root directory of the project")

class FileListingNode:
    def __init__(self, claude_api: ClaudeAPIWrapper):
        self.claude_api = claude_api

    def process(self, project_root: str) -> Dict[str, Any]:
        try:
            self.project_root = Path(project_root)
            logger.info(f"Processing project root: {self.project_root}")
            ignore_spec = self.get_ignore_spec()
            project_files = self.list_project_files(ignore_spec)
            logger.info(f"Found {len(project_files)} files in the project")
            context = self.build_context(project_files)

            return {
                'project_files': project_files,
                'excluded_files': [str(pat) for pat in ignore_spec.patterns],
                'context': context
            }
        except Exception as e:
            logger.error(f"Error in FileListingNode: {str(e)}", exc_info=True)
            return {'error': str(e)}

    def get_ignore_spec(self) -> pathspec.PathSpec:
        patterns = []
        gitignore_path = self.project_root / '.gitignore'
        if gitignore_path.exists():
            with gitignore_path.open('r') as f:
                patterns.extend(f.read().splitlines())
            logger.info(f"Read .gitignore and compiled {len(patterns)} ignore patterns: {patterns}")
        else:
            logger.warning(".gitignore file not found.")

        default_ignores = [
            '.git/', '.hg/', '.svn/', '.idea/', '*.egg-info/',
            '__pycache__/', '.DS_Store', '*.pyc', '.venv/',
            'env/', 'build/', 'dist/', 'node_modules/',
            '*.log', '*.tmp',
        ]
        patterns.extend(default_ignores)
        logger.info(f"Total ignore patterns: {patterns}")
        return pathspec.PathSpec.from_lines('gitwildmatch', patterns)

    def list_project_files(self, ignore_spec: pathspec.PathSpec) -> List[str]:
        project_files = []
        for root, dirs, files in os.walk(self.project_root):
            root_path = Path(root)
            rel_root = root_path.relative_to(self.project_root)
            logger.debug(f"Processing directory: {rel_root}")

            for dir in dirs[:]:
                if ignore_spec.match_file(str(rel_root / dir) + '/'):
                    logger.debug(f"Ignoring directory: {rel_root / dir}")
                    dirs.remove(dir)

            for file in files:
                rel_path = rel_root / file
                if ignore_spec.match_file(str(rel_path)):
                    logger.debug(f"Ignoring file: {rel_path}")
                else:
                    logger.debug(f"Adding file: {rel_path}")
                    project_files.append(str(rel_path))

        logger.info(f"Total files found: {len(project_files)}")
        return project_files

    def build_context(self, project_files: List[str]) -> str:
        context = "Project Files:\n"
        context += "\n".join(project_files)
        context += "\n\nFile Contents:\n"

        for file in project_files:
            file_path = self.project_root / file
            logger.debug(f"Processing file: {file}")
            try:
                with file_path.open('r', encoding='utf-8') as f:
                    content = f.read()
                context += f'\n\n#File {file}:\n{content}'
                logger.debug(f"Successfully read file: {file}")
            except Exception as e:
                logger.warning(f"Could not read file {file}: {str(e)}", exc_info=True)
                context += f'\n\n#File {file}: [Error reading file: {str(e)}]'

        logger.info(f"Final context size: {len(context)} bytes")
        return context


def file_listing(state: Dict[str, Any], args: FileListingArgs) -> Dict[str, Any]:
    file_lister = FileListingNode(state['claude_api'])
    result = file_lister.process(args.project_root)
    state.update(result)
    return state


file_listing_tools = [
    Tool.from_function(
        func=file_listing,
        name="file_listing",
        description="List project files and build context",
        args_schema=FileListingArgs
    )
]

file_listing_node = ToolNode(file_listing_tools)
