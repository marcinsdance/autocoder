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
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

# Import new nodes
from .nodes.analyze_file_listing_node import analyze_file_listing_node
from .nodes.llm_analyze_node import create_llm_analyze_node

logger = logging.getLogger(__name__)

class LangGraphWorkflow:
    def __init__(self, api_key: str):
        self.claude_api = ClaudeAPIWrapper(api_key).client
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
            self._handle_task_execution_result,  # Changed from _handle_task_result
            {True: END, False: "error_handling"}
        )
        workflow.add_edge("error_handling", "task_execution")

        return workflow.compile()

    def _build_analyze_graph(self) -> StateGraph:
        workflow = StateGraph(State)

        # Define nodes
        workflow.add_node("analyze_file_listing", analyze_file_listing_node)
        workflow.add_node("llm_analyze", create_llm_analyze_node(self.claude_api))

        # Define edges
        workflow.set_entry_point("analyze_file_listing")
        workflow.add_edge("analyze_file_listing", "llm_analyze")

        # Add a conditional edge to end the workflow
        workflow.add_conditional_edges(
            "llm_analyze",
            self._handle_analysis_result,
            {
                True: END,
                False: "analyze_file_listing"  # Loop back if analysis is not complete
            }
        )

        return workflow.compile()

    def execute_analysis(self, config: Dict[str, Any] = None) -> str:
        try:
            initial_state = State(
                messages=[AIMessage(content="Please analyze the project.")],  # Changed to AIMessage
                project_root=config.get("project_root", ""),
                context="",
                analysis_result="",
                error=None
            )
            logger.info(f"Initial state: {initial_state}")
            state = initial_state
            for event in self.analyze_graph.stream(initial_state, config):
                state.update(event)
                logger.info(f"Event received: {event}")
                if "error" in event:
                    logger.error(f"Error in event: {event['error']}")
                    return f"An error occurred: {event['error']}"
                elif "messages" in event:
                    logger.debug(f"Received messages: {event['messages']}")
                    for i, message in enumerate(event["messages"]):
                        logger.debug(f"Message {i} type: {type(message)}")
                        if not isinstance(message, BaseMessage):
                            logger.warning(f"Message {i} is not a BaseMessage instance: {type(message)}")
                            if isinstance(message, dict):
                                content = message.get('content', str(message))
                                role = message.get('role', 'AI')
                                if role.lower() == 'human':
                                    event["messages"][i] = HumanMessage(content=content)
                                elif role.lower() == 'system':
                                    event["messages"][i] = SystemMessage(content=content)
                                else:
                                    event["messages"][i] = AIMessage(content=content)
                            else:
                                event["messages"][i] = AIMessage(content=str(message))
                    last_message = event["messages"][-1]
                    logger.info(f"Last message type: {type(last_message)}")
                    logger.info(f"Last message: {last_message.content}")
                elif "analysis_result" in event:
                    logger.info("Received analysis result")
                    print("LLM Analysis of the Project:")
                    print(event["analysis_result"])
                    return "Analysis completed."

            if "analysis_result" in state:
                logger.info("Final analysis result found")
                print("Final LLM Analysis of the Project:")
                print(state["analysis_result"])
                return "Analysis completed."
            else:
                logger.warning("No analysis result was generated")
                print("No analysis result was generated.")
                return "Analysis completed with no result."
        except Exception as e:
            logger.exception(f"An unexpected error occurred during analysis: {str(e)}")
            return f"An unexpected error occurred during analysis: {str(e)}"

    def _handle_analysis_result(self, state: State) -> bool:
        # Check if we have an analysis result and it's not empty
        return 'analysis_result' in state and bool(state['analysis_result'])

    def _handle_task_execution_result(self, state: State) -> bool:
        """
        Determines whether the task execution is complete based on the current state.

        Args:
        state (State): The current state of the workflow.

        Returns:
        bool: True if the task is completed, False otherwise.
        """
        logger.debug(f"Handling task execution result. Current state: {state}")

        # Check if there's an error in the state
        if state.get("error"):
            logger.error(f"Error encountered during task execution: {state['error']}")
            return False

        # Check if the task is marked as completed
        if state.get("task_completed"):
            logger.info("Task marked as completed.")
            return True

        # Check if we have a final result or output
        if state.get("final_result") or state.get("output"):
            logger.info("Final result or output found. Considering task as completed.")
            return True

        # Check if we've reached a maximum number of iterations
        max_iterations = state.get("max_iterations", 5)  # Default to 5 if not set
        current_iteration = state.get("current_iteration", 0)
        if current_iteration >= max_iterations:
            logger.warning(f"Reached maximum iterations ({max_iterations}). Ending task execution.")
            return True

        # If none of the above conditions are met, continue the task execution
        logger.info("Task execution continuing.")
        return False

    def execute(self, task_description: str, config: Dict[str, Any] = None) -> str:
        try:
            initial_state = State(
                messages=[HumanMessage(content=task_description)],
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
                    for i, message in enumerate(event["messages"]):
                        if not isinstance(message, BaseMessage):
                            if isinstance(message, dict):
                                content = message.get('content', str(message))
                                role = message.get('role', 'AI')
                                if role.lower() == 'human':
                                    event["messages"][i] = HumanMessage(content=content)
                                elif role.lower() == 'system':
                                    event["messages"][i] = SystemMessage(content=content)
                                else:
                                    event["messages"][i] = AIMessage(content=content)
                            else:
                                event["messages"][i] = AIMessage(content=str(message))
                    last_message = event["messages"][-1]
                    print(f"AI: {last_message.content}")
            return "Task execution completed."
        except Exception as e:
            logger.exception(f"An unexpected error occurred: {str(e)}")
            return f"An unexpected error occurred: {str(e)}"

