#!/usr/bin/env python3
import argparse
import logging
import os
import sys

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from autocoder.config import Config
from autocoder.file_manager import FileManager
from autocoder.context_builder import ContextBuilder
from autocoder.task_interpreter import TaskInterpreter
from autocoder.code_modifier import CodeModifier
from autocoder.test_runner import TestRunner
from autocoder.error_handler import ErrorHandler
from autocoder.claude_api_wrapper import ClaudeAPIWrapper
from autocoder.langgraph_workflow import LangGraphWorkflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Claude Automated Coding")
    parser.add_argument("task", help="The task description for the automated coding process")
    args = parser.parse_args()

    # Initialize configuration
    config = Config()
    project_dir = config.get_project_directory()
    logger.info(f"Using project directory: {project_dir}")

    # Initialize components
    file_manager = FileManager(project_dir)
    context_builder = ContextBuilder()
    task_interpreter = TaskInterpreter()
    code_modifier = CodeModifier()
    test_runner = TestRunner(project_dir)
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
