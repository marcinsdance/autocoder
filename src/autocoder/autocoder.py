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
from .nodes.tools.directory_checker import check_autocoder_dir, display_init_message, init_autocoder, \
    display_usage_message
from .nodes.file_listing_node import FileListingNode

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def initialize_autocoder():
    logger.info("Starting Autocoder initialization...")
    init_autocoder()
    logger.info("Autocoder directory initialized. Now initializing file listing...")
    result = initialize_file_listing()
    if isinstance(result, dict) and result.get('error'):
        logger.error(f"Autocoder initialization failed: {result['error']}")
        print(f"Error: {result['error']}")
        return False
    logger.info("Autocoder initialization complete.")
    return True


def initialize_file_listing():
    project_root = os.getcwd()
    logger.debug(f"Current working directory: {project_root}")

    # Load environment variables
    load_dotenv()
    print("Environment variables:", os.environ)
    print("ANTHROPIC_API_KEY:", os.getenv('ANTHROPIC_API_KEY'))
    print("CLAUDE_API_KEY:", os.getenv('CLAUDE_API_KEY'))
    print("OPENAI_API_KEY:", os.getenv('OPENAI_API_KEY'))
    api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('CLAUDE_API_KEY') or os.getenv('OPENAI_API_KEY')
    print("Selected API key:", api_key)

    if not api_key:
        logger.error("No API key found. Cannot proceed with file listing.")
        return {
            'error': "No API key found. Please set ANTHROPIC_API_KEY or CLAUDE_API_KEY in your environment or .env file."}

    try:
        logger.debug("Initializing Claude API wrapper...")
        claude_api = ClaudeAPIWrapper(api_key)
        # You might want to add a method to test the API connection here
        # For example: claude_api.test_connection()
    except Exception as e:
        logger.error(f"Failed to initialize Claude API: {str(e)}")
        return {'error': f"Failed to initialize Claude API: {str(e)}"}

    logger.info("Creating FileListingNode...")
    file_lister = FileListingNode(project_root, claude_api)

    state = {"project_root": project_root, "claude_api": claude_api}
    logger.info("Processing file listing...")
    updated_state = file_lister.process(state)

    if updated_state.get('error'):
        return updated_state

    logger.info("File listing process completed successfully.")
    return updated_state


def execute_task(task_description):
    if not check_autocoder_dir():
        logger.error("Autocoder is not initialized in this directory.")
        print("Autocoder is not initialized in this directory. Please run 'autocoder init' first.")
        return

    # Load environment variables
    load_dotenv()
    print("Environment variables:", os.environ)

    # Get API key directly from environment
    api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('CLAUDE_API_KEY') or os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("No API key found. Cannot proceed with task execution.")
        print(
            "Error: No API key found. Please set ANTHROPIC_API_KEY or CLAUDE_API_KEY in your environment or .env file.")
        return

    try:
        claude_api = ClaudeAPIWrapper(api_key)
    except Exception as e:
        logger.error(f"Failed to initialize Claude API: {str(e)}")
        print(f"Error: Failed to initialize Claude API: {str(e)}")
        return

    # Initialize components
    project_root = os.getcwd()
    file_manager = FileManager(project_root)
    context_builder = ContextBuilder()
    task_interpreter = TaskInterpreter()
    code_modifier = CodeModifier()
    test_runner = TestRunner()
    error_handler = ErrorHandler()

    # Initialize LangGraph workflow
    workflow = LangGraphWorkflow(
        file_manager, context_builder, task_interpreter,
        code_modifier, test_runner, error_handler, claude_api
    )

    # Execute workflow
    result = workflow.execute(task_description)

    print(result)

    # Create debug context if DEBUG mode is enabled
    if file_manager.is_debug_mode():
        file_manager.create_debug_context()


def main():
    parser = argparse.ArgumentParser(description="Claude Automated Coding")
    parser.add_argument("command", nargs='?', default="help", choices=["init", "task", "help"],
                        help="Command to execute")
    parser.add_argument("task_description", nargs='?', default="",
                        help="The task description for the automated coding process")
    args = parser.parse_args()

    logger.debug(f"Received command: {args.command}")

    if args.command == "init":
        logger.info("Initializing Autocoder...")
        if not initialize_autocoder():
            return
    elif args.command == "task":
        if args.task_description:
            logger.info(f"Executing task: {args.task_description}")
            execute_task(args.task_description)
        else:
            logger.error("No task description provided for 'task' command.")
            print("Error: Task description is required for the 'task' command.")
            display_usage_message()
    elif args.command == "help" or not args.command:
        if check_autocoder_dir():
            logger.info("Displaying usage message for initialized directory.")
            display_usage_message()
        else:
            logger.info("Displaying initialization message for uninitialized directory.")
            display_init_message()
    else:
        logger.error(f"Unknown command: {args.command}")
        print(f"Unknown command: {args.command}")
        display_usage_message()


if __name__ == "__main__":
    main()
