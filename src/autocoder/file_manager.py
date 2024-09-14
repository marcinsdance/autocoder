import os
from typing import Dict, List
from langchain_core.tools import Tool
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

class ReadFileArgs(BaseModel):
    file_path: str = Field(..., description="Path to the file to read")

class WriteFileArgs(BaseModel):
    file_path: str = Field(..., description="Path to the file to write")
    content: str = Field(..., description="Content to write to the file")

def read_file(state: Dict, args: ReadFileArgs) -> Dict:
    project_root = state.get("project_root", "")
    with open(os.path.join(project_root, args.file_path), 'r') as file:
        content = file.read()
    return {"content": content}

def write_file(state: Dict, args: WriteFileArgs) -> Dict:
    project_root = state.get("project_root", "")
    with open(os.path.join(project_root, args.file_path), 'w') as file:
        file.write(args.content)
    return {"status": "success"}

def list_files(state: Dict) -> Dict:
    project_root = state.get("project_root", "")
    file_list = []
    for root, _, files in os.walk(project_root):
        for file in files:
            file_list.append(os.path.relpath(os.path.join(root, file), project_root))
    return {"files": file_list}

file_manager_tools = [
    Tool.from_function(
        func=read_file,
        name="read_file",
        description="Read the contents of a file",
        args_schema=ReadFileArgs
    ),
    Tool.from_function(
        func=write_file,
        name="write_file",
        description="Write content to a file",
        args_schema=WriteFileArgs
    ),
    Tool.from_function(
        func=list_files,
        name="list_files",
        description="List all files in the project"
    )
]

file_manager_node = ToolNode(file_manager_tools)
