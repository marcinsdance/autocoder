from typing import Annotated, TypedDict, List, Dict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    files: Dict[str, str]
    context: str
    interpreted_task: Dict[str, any]
    modifications: str
    test_results: str
    project_root: str
    autocoder_dir_exists: bool
