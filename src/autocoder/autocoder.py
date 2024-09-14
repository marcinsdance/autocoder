#!/usr/bin/env python3

import argparse
import logging
import os
from dotenv import load_dotenv
from typing import Dict, Any

from .langgraph_workflow import LangGraphWorkflow
from .claude_api_wrapper import ClaudeAPIWrapper
from .nodes.tools.directory_checker import check_autocoder_dir, display_init_message, init_autocoder, \
    display_usage_message
from .file_listing.file_listing_node import FileListingNode
from .error_handler import ErrorHandler

logging.basicConfig(level=logging.INFO)
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
    api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('CLAUDE_API_KEY')
    if not api_key:
        logger.error("No API key found. Cannot proceed with file listing.")
        return {'error': "No API key found. Please set ANTHROPIC_API_KEY or CLAUDE_API_KEY in your environment or .env file."}

    try:
        logger.debug("Initializing Claude API wrapper...")
        claude_api = ClaudeAPIWrapper(api_key)
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

def stream_execution(workflow: LangGraphWorkflow, task_description: str, config: Dict[str, Any]):
    try:
        for event in workflow.graph.stream({
            "messages": [{"role": "user", "content": task_description}],
            "project_root": config.get("project_root", ""),
            "files": {},
            "context": "",
            "interpreted_task": {},
            "modifications": "",
            "test_results": {"success": False, "details": ""}
        }, config):
            if "error" in event:
                yield f"An error occurred: {event['error']['error_message']}"
            elif "messages" in event:
                yield f"Output: {event['messages'][-1]['content']}"
            else:
                yield f"Event: {event}"
    except Exception as e:
        error_report = ErrorHandler.handle_error(e)
        ErrorHandler.log_error(e)
        yield f"An unexpected error occurred: {error_report['error_message']}"

def execute_task(task_description):
    if not check_autocoder_dir():
        logger.error("Autocoder is not initialized in this directory.")
        print("Autocoder is not initialized in this directory. Please run 'autocoder init' first.")
        return

    # Load environment variables
    load_dotenv()

    # Get API key directly from environment
    api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('CLAUDE_API_KEY')
    if not api_key:
        logger.error("No API key found. Cannot proceed with task execution.")
        print("Error: No API key found. Please set ANTHROPIC_API_KEY or CLAUDE_API_KEY in your environment or .env file.")
        return

    try:
        # Initialize LangGraph workflow
        workflow = LangGraphWorkflow(api_key)

        # Execute workflow and stream results
        print("Executing task. Streaming output:")
        for output in stream_execution(workflow, task_description, {"project_root": os.getcwd()}):
            print(output)

    except Exception as e:
        logger.error(f"Failed to execute task: {str(e)}")
        print(f"Error: Failed to execute task: {str(e)}")

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
