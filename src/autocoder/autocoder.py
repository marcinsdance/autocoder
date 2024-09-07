#!/usr/bin/env python3

import argparse
import logging
import os
from dotenv import load_dotenv

from .file_manager import FileManager
from .context_builder import ContextBuilder
from .task_interpreter import TaskInterpreter
from .code_modifier import CodeModifier
from .test_runner import TestRunner
from .error_handler import ErrorHandler
from .claude_api_wrapper import ClaudeAPIWrapper
from .langgraph_workflow import LangGraphWorkflow
from .nodes.tools.directory_checker import check_autocoder_dir, display_init_message, init_autocoder, display_usage_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Claude Automated Coding")
    parser.add_argument("command", nargs='?', default="help", choices=["init", "task", "help"], help="Command to execute")
    parser.add_argument("task_description", nargs='?', default="", help="The task description for the automated coding process")
    args = parser.parse_args()

    if args.command == "init":
        init_autocoder()
        return

    if args.command == "help" or (args.command == "task" and not args.task_description):
        if check_autocoder_dir():
            display_usage_message()
        else:
            display_init_message()
        return

    if args.command == "task":
        if not check_autocoder_dir():
            display_init_message()
            return

        # Load environment variables
        load_dotenv()

        # Get API key directly from environment
        api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('CLAUDE_API_KEY')
        if not api_key:
            raise ValueError(
                "Neither ANTHROPIC_API_KEY nor CLAUDE_API_KEY is set in the environment variables or .env file")

        # Initialize components
        project_root = os.getcwd()
        file_manager = FileManager(project_root)
        context_builder = ContextBuilder()
        task_interpreter = TaskInterpreter()
        code_modifier = CodeModifier()
        test_runner = TestRunner()
        error_handler = ErrorHandler()
        claude_api = ClaudeAPIWrapper(api_key)

        # Initialize LangGraph workflow
        workflow = LangGraphWorkflow(
            file_manager, context_builder, task_interpreter,
            code_modifier, test_runner, error_handler, claude_api
        )

        # Execute workflow
        result = workflow.execute(args.task_description)

        print(result)

        # Create debug context if DEBUG mode is enabled
        if file_manager.is_debug_mode():
            file_manager.create_debug_context()

    if __name__ == "__main__":
        main()
