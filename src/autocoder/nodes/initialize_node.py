from typing import Dict
from langchain_core.tools import Tool
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel

class InitializeArgs(BaseModel):
    pass

def initialize(state: Dict, args: InitializeArgs) -> Dict:
    # Perform any necessary initialization
    state["initialized"] = True
    return state

initialize_tools = [
    Tool.from_function(
        func=initialize,
        name="initialize",
        description="Initialize the Autocoder system",
        args_schema=InitializeArgs
    )
]

initialize_node = ToolNode(initialize_tools)
