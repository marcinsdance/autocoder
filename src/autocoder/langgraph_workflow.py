import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from .state import State
from .file_manager import file_manager_node
from .context_builder import context_builder_node
from .task_interpreter import task_interpreter_node
from .code_modifier import code_modifier_node
from .test_runner import test_runner_node
from .error_handler import ErrorHandler

logger = logging.getLogger(__name__)

class LangGraphWorkflow:
    def __init__(self, claude_api):
        self.claude_api = claude_api
        self.graph = self._build_graph()
        self.memory = MemorySaver()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(State)

        # Define nodes
        workflow.add_node("file_manager", file_manager_node)
        workflow.add_node("context_builder", context_builder_node)
        workflow.add_node("task_interpreter", task_interpreter_node)
        workflow.add_node("code_modifier", code_modifier_node)
        workflow.add_node("test_runner", test_runner_node)

        # Define edges
        workflow.set_entry_point("task_interpreter")
        workflow.add_edge("task_interpreter", "file_manager")
        workflow.add_edge("file_manager", "context_builder")
        workflow.add_edge("context_builder", "code_modifier")
        workflow.add_edge("code_modifier", "file_manager")
        workflow.add_edge("file_manager", "test_runner")
        workflow.add_conditional_edges(
            "test_runner",
            self._handle_test_results,
            {True: END, False: "code_modifier"}
        )

        return workflow.compile()

    def _handle_test_results(self, state: State) -> bool:
        if state["test_results"]["success"]:
            logger.info("Task completed successfully")
            return True
        else:
            error_report = ErrorHandler.handle_error(state["test_results"]["details"])
            logger.warning("Tests failed. See error report for details.")
            return False

    def execute(self, task_description: str, config: Dict[str, Any] = None) -> str:
        try:
            initial_state = State(
                messages=[("user", task_description)],
                project_root=config.get("project_root", ""),
                claude_api=self.claude_api,
                files={},
                context="",
                interpreted_task={},
                modifications="",
                test_results={"success": False, "details": ""}
            )
            for event in self.graph.stream(initial_state, config):
                if "error" in event:
                    return f"An error occurred: {event['error']['error_message']}"
                if "messages" in event:
                    print(event["messages"][-1])
            return "Task execution completed."
        except Exception as e:
            error_report = ErrorHandler.handle_error(e)
            ErrorHandler.log_error(e)
            return f"An unexpected error occurred: {error_report['error_message']}"
