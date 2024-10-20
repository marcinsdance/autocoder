import logging
from typing import Dict, Any
from ..file_manager import FileManager
from langchain_core.tools import Tool
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from ..claude_api_wrapper import ClaudeAPIWrapper

logger = logging.getLogger(__name__)


class FileListingArgs(BaseModel):
    project_root: str = Field(..., description="Root directory of the project")


class FileListingNode:
    def __init__(self, claude_api: ClaudeAPIWrapper):
        self.claude_api = claude_api

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            project_root = state.get('project_root')
            if not project_root:
                raise ValueError("Project root is not specified in the state")

            file_manager = FileManager(project_root)

            project_files = file_manager.list_files()
            context = self.build_context(file_manager)

            return {
                'project_files': project_files,
                'context': context
            }
        except Exception as e:
            logger.error(f"Error in FileListingNode: {str(e)}", exc_info=True)
            return {'error': str(e)}

    def build_context(self, file_manager: FileManager) -> str:
        try:
            context = "Project Files:\n"
            context += "\n".join(file_manager.list_files())
            context += "\n\nFile Contents:\n"

            for file_path in file_manager.list_files():
                try:
                    content = file_manager.read_file(file_path)
                    context += f'\n\n#File {file_path}:\n{content}'
                except Exception as e:
                    logger.warning(f"Could not read file {file_path}: {str(e)}")
                    context += f'\n\n#File {file_path}: [Error reading file: {str(e)}]'

            return context
        except Exception as e:
            logger.error(f"Error building context: {str(e)}", exc_info=True)
            return f"Error building context: {str(e)}"


def file_listing(state: Dict[str, Any], args: FileListingArgs) -> Dict[str, Any]:
    try:
        claude_api = state.get('claude_api')
        if not claude_api:
            raise ValueError("Claude API is not specified in the state")

        file_lister = FileListingNode(claude_api)
        result = file_lister.process(state)
        state.update(result)
        return state
    except Exception as e:
        logger.error(f"Error in file_listing: {str(e)}", exc_info=True)
        return {'error': str(e)}


file_listing_tools = [
    Tool.from_function(
        func=file_listing,
        name="file_listing",
        description="List project files and build context",
        args_schema=FileListingArgs
    )
]

file_listing_node = ToolNode(file_listing_tools)
