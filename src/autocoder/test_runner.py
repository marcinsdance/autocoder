import subprocess
from typing import Dict
from langchain_core.tools import Tool
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel

class TestRunnerArgs(BaseModel):
    pass  # No arguments needed for test runner

def test_runner(state: Dict, args: TestRunnerArgs) -> Dict:
    try:
        result = subprocess.run(['pytest'], capture_output=True, text=True)
        if result.returncode == 0:
            return {"success": True, "details": "All tests passed"}
        else:
            return {"success": False, "details": result.stderr}
    except Exception as e:
        return {"success": False, "details": f"Error running tests: {str(e)}"}

test_runner_tools = [
    Tool.from_function(
        func=test_runner,
        name="test_runner",
        description="Run tests for the project",
        args_schema=TestRunnerArgs
    )
]

test_runner_node = ToolNode(test_runner_tools)
