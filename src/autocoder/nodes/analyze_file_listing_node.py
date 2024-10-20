import os
import logging
from pathlib import Path
import pathspec
from typing import Dict, List
from langchain_core.tools import Tool
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage

logger = logging.getLogger(__name__)

class AnalyzeFileListingArgs(BaseModel):
    project_root: str = Field(..., description="Root directory of the project")

class AnalyzeFileListingNode:
    @staticmethod
    def process(state: Dict, args: AnalyzeFileListingArgs) -> Dict:
        try:
            project_root = Path(args.project_root)
            ignore_spec = AnalyzeFileListingNode.get_ignore_spec(project_root)
            project_files = AnalyzeFileListingNode.list_project_files(project_root, ignore_spec)
            context = AnalyzeFileListingNode.build_context(project_root, project_files)

            state.update({
                'project_files': project_files,
                'excluded_files': [str(pat) for pat in ignore_spec.patterns],
                'context': context,
                'messages': state.get('messages', []) + [AIMessage(content="File listing and context building completed.")]
            })

            logger.info(f"File listing completed for analysis. Found {len(project_files)} files.")
            return state
        except Exception as e:
            logger.error(f"Error in AnalyzeFileListingNode: {str(e)}")
            state['error'] = str(e)
            state['messages'] = state.get('messages', []) + [AIMessage(content=f"Error: {str(e)}")]
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
        context = "Project Files:\n"
        context += "\n".join(project_files)
        context += "\n\nFile Contents:\n"

        for file in project_files:
            file_path = project_root / file
            try:
                with file_path.open('r', encoding='utf-8') as f:
                    content = f.read()
                context += f'\n\n#File {file}:\n{content}'
            except Exception as e:
                logger.warning(f"Could not read file {file}: {str(e)}")

        return context


def analyze_file_listing(state: Dict, args: AnalyzeFileListingArgs) -> Dict:
    return AnalyzeFileListingNode.process(state, args)


analyze_file_listing_tools = [
    Tool.from_function(
        func=analyze_file_listing,
        name="analyze_file_listing",
        description="List project files and build context for analysis",
        args_schema=AnalyzeFileListingArgs
    )
]

analyze_file_listing_node = ToolNode(analyze_file_listing_tools)
