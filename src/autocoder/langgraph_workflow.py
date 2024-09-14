import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from .state import State
from .nodes.file_listing_node import file_listing_node
from .nodes.initialize_node import initialize_node
from .nodes.task_execution_node import task_execution_node
from .nodes.error_handling_node import error_handling_node
from .claude_api_wrapper import claude_api_node, ClaudeAPIWrapper

logger = logging.getLogger(__name__)

class LangGraphWorkflow:
    def __init__(self, api_key: str):
        self.claude_api = ClaudeAPIWrapper(api_key)
        self.graph = self._build_graph()
        self.memory = MemorySaver()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(State)

        # Define nodes
        workflow.add_node("initialize", initialize_node)
        workflow.add_node("file_listing", file_listing_node)
        workflow.add_node("task_execution", task_execution_node)
        workflow.add_node("claude_api", claude_api_node)
        workflow.add_node("error_handling", error_handling_node)

        # Define edges
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "file_listing")
        workflow.add_edge("file_listing", "task_execution")
        workflow.add_edge("task_execution", "claude_api")
        workflow.add_edge("claude_api", "task_execution")
        workflow.add_conditional_edges(
            "task_execution",
            self._handle_task_result,
            {True: END, False: "error_handling"}
        )
        workflow.add_edge("error_handling", "task_execution")

        return workflow.compile()

    def _handle_task_result(self, state: State) -> bool:
        return state["task_completed"]

    def execute(self, task_description: str, config: Dict[str, Any] = None) -> str:
        try:
            initial_state = State(
                messages=[{"role": "user", "content": task_description}],
                project_root=config.get("project_root", ""),
                claude_api=self.claude_api,
                files={},
                context="",
                task_completed=False,
                error=None
            )
            for event in self.graph.stream(initial_state, config):
                if "error" in event:
                    return f"An error occurred: {event['error']}"
                if "messages" in event:
                    print(event["messages"][-1])
            return "Task execution completed."
        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")
            return f"An unexpected error occurred: {str(e)}"
