# File: src/autocoder/nodes/task_execution_node.py

from typing import Dict
from langchain_core.tools import Tool
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from functools import partial


class TaskExecutionArgs(BaseModel):
    task_description: str = Field(..., description="Description of the task to execute")


def execute_task(state: Dict, args: TaskExecutionArgs, claude_api) -> Dict:
    try:
        # Build the prompt using the task description and context
        prompt = f"{HUMAN_PROMPT} Based on the following context, please perform the task: {args.task_description}\n\nContext:\n{state['context']}\n{AI_PROMPT}"

        # Call the LLM
        response = claude_api.completions.create(
            model="claude-instant-v1",
            prompt=prompt,
            max_tokens_to_sample=1000,
            stop_sequences=[HUMAN_PROMPT]
        )

        # Process the response
        state["task_result"] = response.completion.strip()
        state["task_completed"] = True
        return state
    except Exception as e:
        state["error"] = f"Error during task execution: {str(e)}"
        return state


def create_task_execution_node(claude_api):
    execute_task_partial = partial(execute_task, claude_api=claude_api)
    task_execution_tools = [
        Tool.from_function(
            func=execute_task_partial,
            name="execute_task",
            description="Execute the given task",
            args_schema=TaskExecutionArgs
        )
    ]
    return ToolNode(task_execution_tools)
