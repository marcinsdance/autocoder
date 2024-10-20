import os
from typing import Dict, List
from langchain_core.tools import Tool
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
import re


class ReadFileArgs(BaseModel):
    file_path: str = Field(..., description="Path to the file to read")

class WriteFileArgs(BaseModel):
    file_path: str = Field(..., description="Path to the file to write")
    content: str = Field(..., description="Content to write to the file")

class FileManager:
    def __init__(self, project_root):
        self.project_root = project_root

    def read_file(self, file_path: str) -> str:
        with open(os.path.join(self.project_root, file_path), 'r') as file:
            return file.read()

    def write_file(self, file_path: str, content: str):
        full_path = os.path.join(self.project_root, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as file:
            file.write(content)

    def list_files(self) -> List[str]:
        file_list = []
        for root, _, files in os.walk(self.project_root):
            for file in files:
                file_list.append(os.path.relpath(os.path.join(root, file), self.project_root))
        return file_list

    def filter_relevant_files(self, task_description: str, max_files: int = 10) -> List[str]:
        all_files = self.list_files()
        relevant_files = []

        # Extract potential file names or patterns from the task description
        potential_files = re.findall(r'\b[\w-]+\.[\w-]+\b', task_description)
        potential_patterns = [f".*{pattern}.*" for pattern in potential_files]

        # First, add files that directly match the task description
        for file in all_files:
            if any(pattern.lower() in file.lower() for pattern in potential_files):
                relevant_files.append(file)
                if len(relevant_files) >= max_files:
                    break

        # Then, add files that match the extracted patterns
        if len(relevant_files) < max_files:
            for file in all_files:
                if any(re.match(pattern, file, re.IGNORECASE) for pattern in potential_patterns):
                    if file not in relevant_files:
                        relevant_files.append(file)
                        if len(relevant_files) >= max_files:
                            break

        # If we still haven't reached max_files, add files based on common extensions
        if len(relevant_files) < max_files:
            common_extensions = ['.py', '.js', '.html', '.css', '.md']
            for ext in common_extensions:
                for file in all_files:
                    if file.endswith(ext) and file not in relevant_files:
                        relevant_files.append(file)
                        if len(relevant_files) >= max_files:
                            break
                if len(relevant_files) >= max_files:
                    break

        # Print the list of filtered files
        print("Filtered relevant files:")
        for file in relevant_files:
            print(f"  - {file}")

        return relevant_files


def read_file(state: Dict, args: ReadFileArgs) -> Dict:
    project_root = state.get("project_root", "")
    file_manager = FileManager(project_root)
    content = file_manager.read_file(args.file_path)
    return {"content": content}


def write_file(state: Dict, args: WriteFileArgs) -> Dict:
    project_root = state.get("project_root", "")
    file_manager = FileManager(project_root)
    file_manager.write_file(args.file_path, args.content)
    return {"status": "success"}

def list_files(state: Dict) -> Dict:
    project_root = state.get("project_root", "")
    file_manager = FileManager(project_root)
    file_list = file_manager.list_files()
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
