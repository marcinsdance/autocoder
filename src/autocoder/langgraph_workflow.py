import logging
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from .state import State

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

    def _build_graph(self):
        graph = StateGraph(State)
        graph.add_node("interpret_task", self._interpret_task)
        graph.add_node("build_context", self._build_context)
        graph.add_node("generate_modifications", self._generate_modifications)
        graph.add_node("apply_modifications", self._apply_modifications)
        graph.add_node("run_tests", self._run_tests)

        graph.add_edge(START, "interpret_task")
        graph.add_edge("interpret_task", "build_context")
        graph.add_edge("build_context", "generate_modifications")
        graph.add_edge("generate_modifications", "apply_modifications")
        graph.add_edge("apply_modifications", "run_tests")
        graph.add_conditional_edges(
            "run_tests",
            self._handle_test_results,
            {True: "__end__", False: "generate_modifications"}
        )

        return graph.compile(checkpointer=self.memory)

    def _interpret_task(self, state: State):
        interpreted_task = self.task_interpreter.interpret_task(state["messages"][-1].content)
        logger.info(f"Task interpreted: {interpreted_task['task_type']}")
        return {"interpreted_task": interpreted_task}

    def _build_context(self, state: State):
        files = self.file_manager.list_files()
        file_contents = {f: self.file_manager.read_file(f) for f in files}
        context = self.context_builder.build_context(file_contents)
        logger.info("Context built successfully")
        return {"files": file_contents, "context": context}

    def _generate_modifications(self, state: State):
        task_prompt = self.task_interpreter.get_prompt_for_task(state["interpreted_task"])
        full_prompt = f"Context:\n{state['context']}\n\nTask:\n{task_prompt}"
        modifications = self.claude_api.generate_response(full_prompt)
        logger.info("Received response from Claude API")
        return {"modifications": modifications}

    def _apply_modifications(self, state: State):
        for file in state["interpreted_task"]["affected_files"]:
            if file in state["files"]:
                original_code = state["files"][file]
                modified_code = self.code_modifier.modify_code(original_code, state["modifications"])
                self.file_manager.write_file(file, modified_code)
                logger.info(f"Modified file: {file}")
        return {}

    def _run_tests(self, state: State):
        success, test_result = self.test_runner.run_tests()
        return {"test_results": test_result}

    def _handle_test_results(self, state: State):
        if "success" in state["test_results"]:
            logger.info("Task completed successfully")
            return True
        else:
            error_report = self.error_handler.handle_error(state["test_results"])
            logger.warning("Tests failed. See error report for details.")
            return False

    def execute(self, task_description, config=None):
        try:
            initial_state = {"messages": [("user", task_description)]}
            for event in self.graph.stream(initial_state, config):
                if "messages" in event:
                    print(event["messages"][-1])
            return "Task execution completed."
        except Exception as e:
            error_report = self.error_handler.handle_error(e)
            self.error_handler.log_error(e)
            return error_report
