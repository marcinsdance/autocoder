import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from .state import State
from .nodes.file_listing_node import file_listing_node
from .nodes.initialize_node import initialize_node
from .nodes.error_handling_node import error_handling_node
from .claude_api_wrapper import ClaudeAPIWrapper
from .nodes.task_execution_node import create_task_execution_node

# Import new nodes
from .nodes.analyze_file_listing_node import analyze_file_listing_node
from .nodes.llm_analyze_node import create_llm_analyze_node

logger = logging.getLogger(__name__)

class LangGraphWorkflow:
    def __init__(self, api_key: str):
        self.claude_api = ClaudeAPIWrapper(api_key).client  # Use the client directly
        self.graph = self._build_graph()
        self.analyze_graph = self._build_analyze_graph()
        self.memory = MemorySaver()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(State)

        # Define nodes
        workflow.add_node("initialize", initialize_node)
        workflow.add_node("file_listing", file_listing_node)
        workflow.add_node("task_execution", create_task_execution_node(self.claude_api))
        workflow.add_node("error_handling", error_handling_node)

        # Define edges
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "file_listing")
        workflow.add_edge("file_listing", "task_execution")
        workflow.add_conditional_edges(
            "task_execution",
            self._handle_task_result,
            {True: END, False: "error_handling"}
        )
        workflow.add_edge("error_handling", "task_execution")

        return workflow.compile()

    def _build_analyze_graph(self) -> StateGraph:
        workflow = StateGraph(State)

        # Define nodes
        workflow.add_node("analyze_file_listing", analyze_file_listing_node)
        workflow.add_node("llm_analyze", create_llm_analyze_node(self.claude_api))
        workflow.add_node("error_handling", error_handling_node)

        # Define edges
        workflow.set_entry_point("analyze_file_listing")
        workflow.add_edge("analyze_file_listing", "llm_analyze")
        workflow.add_conditional_edges(
            "llm_analyze",
            self._handle_analysis_result,
            {True: END, False: "error_handling"}
        )
        workflow.add_edge("error_handling", END)

        return workflow.compile()

    def _handle_analysis_result(self, state: State) -> bool:
        return 'analysis_result' in state

    def execute_analysis(self, config: Dict[str, Any] = None) -> str:
        try:
            initial_state = State(
                project_root=config.get("project_root", ""),
                # Remove 'claude_api' from the state
                context="",
                analysis_result="",
                error=None
            )
            for event in self.analyze_graph.stream(initial_state, config):
                if "error" in event:
                    return f"An error occurred: {event['error']}"
                if "analysis_result" in event:
                    print(event["analysis_result"])
            return "Analysis completed."
        except Exception as e:
            logger.error(f"An unexpected error occurred during analysis: {str(e)}")
            return f"An unexpected error occurred during analysis: {str(e)}"

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
