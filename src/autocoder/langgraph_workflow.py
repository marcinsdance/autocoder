import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from .state import State
from .nodes.check_autocoder_dir import check_autocoder_dir
from .nodes.interpret_task import interpret_task
from .nodes.build_context import build_context
from .nodes.generate_modifications import generate_modifications
from .nodes.apply_modifications import apply_modifications
from .nodes.run_tests import run_tests
from .error_handler import ErrorHandler

logger = logging.getLogger(__name__)

class LangGraphWorkflow:
    def __init__(self, file_manager, context_builder, task_interpreter,
                 code_modifier, test_runner, error_handler, claude_api):
        self.file_manager = file_manager
        self.context_builder = context_builder
        self.task_interpreter = task_interpreter
        self.code_modifier = code_modifier
        self.test_runner = test_runner
        self.error_handler = error_handler
        self.claude_api = claude_api
        self.graph = self._build_graph()
        self.memory = MemorySaver()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(State)

        # Define nodes
        workflow.add_node("check_autocoder_dir", check_autocoder_dir)
        workflow.add_node("interpret_task", interpret_task)
        workflow.add_node("build_context", build_context)
        workflow.add_node("generate_modifications", generate_modifications)
        workflow.add_node("apply_modifications", apply_modifications)
        workflow.add_node("run_tests", run_tests)

        # Define edges
        workflow.set_entry_point("check_autocoder_dir")
        workflow.add_conditional_edges(
            "check_autocoder_dir",
            self._check_initialization,
            {True: "interpret_task", False: END}
        )
        workflow.add_edge("interpret_task", "build_context")
        workflow.add_edge("build_context", "generate_modifications")
        workflow.add_edge("generate_modifications", "apply_modifications")
        workflow.add_edge("apply_modifications", "run_tests")
        workflow.add_conditional_edges(
            "run_tests",
            self._handle_test_results,
            {True: END, False: "generate_modifications"}
        )

        return workflow.compile()

    def _check_initialization(self, state: State) -> bool:
        return state["autocoder_dir_exists"]

    def _handle_test_results(self, state: State) -> bool:
        if state["test_results"]["success"]:
            logger.info("Task completed successfully")
            return True
        else:
            error_report = self.error_handler.handle_error(state["test_results"]["details"])
            logger.warning("Tests failed. See error report for details.")
            return False

    def execute(self, task_description: str, config: Dict[str, Any] = None) -> str:
        try:
            initial_state = State(
                messages=[("user", task_description)],
                project_root=self.file_manager.project_root,
                claude_api=self.claude_api,
                autocoder_dir_exists=False,
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
            error_report = self.error_handler.handle_error(e)
            self.error_handler.log_error(e)
            return f"An unexpected error occurred: {error_report['error_message']}"
