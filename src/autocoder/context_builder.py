from typing import Dict, List
from langchain_core.tools import Tool
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from .file_manager import read_file, ReadFileArgs

class BuildContextArgs(BaseModel):
    files: List[str] = Field(..., description="List of file paths to build context from")

def build_context(state: Dict, args: BuildContextArgs) -> Dict:
    context = ""
    for file in args.files:
        content = read_file(state, ReadFileArgs(file_path=file))["content"]
        context += f"#File {file}:\n{content}\n\n"
    return {"context": context}

context_builder_tools = [
    Tool.from_function(
        func=build_context,
        name="build_context",
        description="Build context from a list of files",
        args_schema=BuildContextArgs
    )
]

context_builder_node = ToolNode(context_builder_tools)
