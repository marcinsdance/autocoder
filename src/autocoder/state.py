from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]
    files: dict
    context: str
    interpreted_task: dict
    modifications: str
    test_results: str
