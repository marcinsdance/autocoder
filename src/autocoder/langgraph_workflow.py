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
from .file_listing.file_listing_node import FileListingNode
from .file_manager import FileManager

logger = logging.getLogger(__name__)


class LangGraphWorkflow:
    def __init__(self, api_key: str):
        self.claude_api = ClaudeAPIWrapper(api_key)
        self.graph = self._build_graph()
        self.memory = MemorySaver()
        self.file_lister = FileListingNode(claude_api=self.claude_api)

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(State)

        # Define nodes
        workflow.add_node("initialize", initialize_node)
        workflow.add_node("file_listing", file_listing_node)
        workflow.add_node("task_execution", create_task_execution_node(self.claude_api.client))
        workflow.add_node("error_handling", error_handling_node)

        # Define edges
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "file_listing")
        workflow.add_edge("file_listing", "task_execution")
        workflow.add_conditional_edges(
            "task_execution",
            self._handle_task_execution_result,
            {True: END, False: "error_handling"}
        )
        workflow.add_edge("error_handling", "task_execution")

        return workflow.compile()

    def execute_analysis(self, config: Dict[str, Any] = None) -> str:
        try:
            project_root = config.get("project_root", "")
            logger.info(f"Analyzing project in: {project_root}")

            file_manager = FileManager(project_root)

            # Get file listing and context
            context = self.build_context(file_manager)

            # Create an initial state for the file listing process
            initial_state = {
                "project_root": project_root,
                "claude_api": self.claude_api,
                "messages": [],
                "context": "",
                "files": {},
                "error": None
            }

            # Get file listing and context
            file_listing_result = self.file_lister.process(initial_state)

            if 'error' in file_listing_result:
                logger.error(f"Error in file listing: {file_listing_result['error']}")
                return f"An error occurred during file listing: {file_listing_result['error']}"

            context = file_listing_result.get('context', '')

            # Prepare the prompt for the LLM
            prompt = f"""Please analyze the following project structure and file contents:

{context}

Provide a comprehensive analysis of the project, including:
1. The overall structure and organization of the project
2. Main components and their purposes
3. Key functionalities implemented
4. Any patterns or architectural decisions you notice
5. Potential areas for improvement or optimization

Your analysis should be detailed and insightful, offering a clear understanding of the project's purpose and implementation."""

            # Call the LLM for analysis
            response = self.claude_api.generate_response(
                state={},  # We don't need to pass any state
                args={
                    "messages": [HumanMessage(content=prompt)],
                    "max_tokens": 2000
                }
            )

            if 'error' in response:
                logger.error(f"Error in LLM analysis: {response['error']}")
                return f"An error occurred during LLM analysis: {response['error']}"

            analysis_result = response['response']
            logger.info("Analysis completed successfully")
            return f"Analysis completed. Results:\n\n{analysis_result}"

        except Exception as e:
            logger.exception(f"An unexpected error occurred during analysis: {str(e)}")
            return f"An unexpected error occurred during analysis: {str(e)}"


    def build_context(self, file_manager: FileManager) -> str:
        context = "Project Files:\n"
        context += "\n".join(file_manager.list_files())
        context += "\n\nFile Contents:\n"

        for file_path in file_manager.list_files():
            try:
                content = file_manager.read_file(file_path)
                context += f'\n\n#File {file_path}:\n{content}'
            except Exception as e:
                logger.warning(f"Could not read file {file_path}: {str(e)}")

        return context


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
                claude_api=self.claude_api.client,
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
