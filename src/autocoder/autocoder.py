#!/usr/bin/env python3
import argparse
import logging

from .config import Config
from .file_manager import FileManager
from .context_builder import ContextBuilder
from .task_interpreter import TaskInterpreter
from .code_modifier import CodeModifier
from .test_runner import TestRunner
from .error_handler import ErrorHandler
from .claude_api_wrapper import ClaudeAPIWrapper
from .langgraph_workflow import LangGraphWorkflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Claude Automated Coding")
    parser.add_argument("task", nargs='?', default="", help="The task description for the automated coding process")
    args = parser.parse_args()

    if not args.task:
        print("Please provide a task description.")
        return

    # Initialize configuration
    config = Config()

    # Initialize components
    file_manager = FileManager()
    context_builder = ContextBuilder()
    task_interpreter = TaskInterpreter()
    code_modifier = CodeModifier()
    test_runner = TestRunner()
    error_handler = ErrorHandler()
    claude_api = ClaudeAPIWrapper(config.get_api_key())

    # Initialize LangGraph workflow
    workflow = LangGraphWorkflow(
        file_manager, context_builder, task_interpreter,
        code_modifier, test_runner, error_handler, claude_api
    )

    # Execute workflow
    result = workflow.execute(args.task)

    print(result)

if __name__ == "__main__":
    main()
