from typing import Dict
from enum import Enum
import re
from langchain_core.tools import Tool
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

class TaskType(Enum):
    ADD_FEATURE = "add_feature"
    FIX_BUG = "fix_bug"
    REFACTOR = "refactor"
    OPTIMIZE = "optimize"
    TEST = "test"
    DOCUMENT = "document"
    UNKNOWN = "unknown"

class TaskInterpreterArgs(BaseModel):
    task_description: str = Field(..., description="Description of the task to interpret")

def task_interpreter(state: Dict, args: TaskInterpreterArgs) -> Dict:
    task_type_keywords = {
        TaskType.ADD_FEATURE: ["add", "create", "implement", "new feature"],
        TaskType.FIX_BUG: ["fix", "bug", "issue", "problem", "error"],
        TaskType.REFACTOR: ["refactor", "restructure", "reorganize"],
        TaskType.OPTIMIZE: ["optimize", "improve performance", "speed up"],
        TaskType.TEST: ["test", "unit test", "integration test"],
        TaskType.DOCUMENT: ["document", "add comments", "explain"]
    }

    task_type = TaskType.UNKNOWN
    for t_type, keywords in task_type_keywords.items():
        if any(keyword in args.task_description.lower() for keyword in keywords):
            task_type = t_type
            break

    file_pattern = r'\b[\w-]+\.(py|js|html|css|md)\b'
    affected_files = list(set(re.findall(file_pattern, args.task_description)))

    subtasks = [subtask.strip() for subtask in args.task_description.split(". ") if subtask.strip()]

    return {
        "task_type": task_type.value,
        "affected_files": affected_files,
        "subtasks": subtasks
    }

task_interpreter_tools = [
    Tool.from_function(
        func=task_interpreter,
        name="task_interpreter",
        description="Interpret a task description",
        args_schema=TaskInterpreterArgs
    )
]

task_interpreter_node = ToolNode(task_interpreter_tools)
