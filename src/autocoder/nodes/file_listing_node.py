# File: src/autocoder/nodes/file_listing_node.py

import os
import logging
from pathlib import Path
import pathspec
from typing import Dict, List
from langchain_core.tools import Tool
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class FileListingArgs(BaseModel):
    project_root: str = Field(..., description="Root directory of the project")

class FileListingNode:
    @staticmethod
    def process(state: Dict, args: FileListingArgs) -> Dict:
        try:
            project_root = Path(args.project_root)
            ignore_spec = FileListingNode.get_ignore_spec(project_root)
            project_files = FileListingNode.list_project_files(project_root, ignore_spec)
            context = FileListingNode.build_context(project_root, project_files)

            state.update({
                'project_files': project_files,
                'excluded_files': [str(pat) for pat in ignore_spec.patterns],
                'context': context
            })

            logger.info(f"File listing completed. Found {len(project_files)} files.")
            return state
        except Exception as e:
            logger.error(f"Error in FileListingNode: {str(e)}")
            state['error'] = str(e)
            return state

    @staticmethod
    def get_ignore_spec(project_root: Path) -> pathspec.PathSpec:
        patterns = []
        gitignore_path = project_root / '.gitignore'
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

    @staticmethod
    def list_project_files(project_root: Path, ignore_spec: pathspec.PathSpec) -> List[str]:
        project_files = []
        for root, dirs, files in os.walk(project_root):
            root_relative = os.path.relpath(root, project_root)
            if root_relative == '.':
                root_relative = ''
            dirs[:] = [d for d in dirs if not ignore_spec.match_file(os.path.join(root_relative, d) + '/')]
            for file in files:
                rel_path = os.path.join(root_relative, file)
                if not ignore_spec.match_file(rel_path):
                    project_files.append(rel_path)
        return project_files

    @staticmethod
    def build_context(project_root: Path, project_files: List[str]) -> str:
        context = ''
        for file in project_files:
            file_path = project_root / file
            try:
                with file_path.open('r', encoding='utf-8') as f:
                    content = f.read()
                context += f'#File {file}:\n{content}\n\n'
            except Exception as e:
                logger.warning(f"Could not read file {file}: {str(e)}")
        return context

def file_listing(state: Dict, args: FileListingArgs) -> Dict:
    return FileListingNode.process(state, args)

file_listing_tools = [
    Tool.from_function(
        func=file_listing,
        name="file_listing",
        description="List project files and build context",
        args_schema=FileListingArgs
    )
]

file_listing_node = ToolNode(file_listing_tools)
