import argparse
import logging
import os
from dotenv import load_dotenv
from typing import Dict, Any
from pathlib import Path

from .langgraph_workflow import LangGraphWorkflow
from .nodes.tools.directory_checker import (
    check_autocoder_dir,
    display_init_message,
    init_autocoder,
    display_usage_message,
)
from .error_handler import ErrorHandler
from .nodes.file_listing_node import FileListingNode, FileListingArgs
from .claude_api_wrapper import ClaudeAPIWrapper
from .file_manager import FileManager
from .file_listing.file_listing_node import FileListingNode
from typing import Dict, Any, List

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def initialize_autocoder():
    logger.info("Starting Autocoder initialization...")
    init_autocoder()
    logger.info("Autocoder initialization complete.")
    return True

def stream_execution(workflow: LangGraphWorkflow, task_description: str, config: Dict[str, Any]):
    try:
        for event in workflow.graph.stream({
            "messages": [{"role": "user", "content": task_description}],
            "project_root": config.get("project_root", ""),
            "files": {},
            "context": "",
            "task_completed": False,
            "error": None
        }, config):
            if "error" in event:
                yield f"An error occurred: {event['error']}"
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

    load_dotenv()
    api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('CLAUDE_API_KEY')
    if not api_key:
        logger.error("No API key found. Cannot proceed with task execution.")
        print(
            "Error: No API key found. Please set ANTHROPIC_API_KEY or CLAUDE_API_KEY in your environment or .env file.")
        return

    try:
        workflow = LangGraphWorkflow(api_key)
        project_root = os.getcwd()

        # Create a FileManager instance
        file_manager = FileManager(project_root)

        # Filter relevant files based on the task description
        relevant_files = file_manager.filter_relevant_files(task_description)

        # Build context only for relevant files
        context = build_context(file_manager, relevant_files)

        # Send context and task description to LLM
        response = workflow.claude_api.generate_response(
            state={},
            args={
                "messages": [
                    {"role": "system",
                     "content": "You are an AI assistant tasked with modifying code based on the given context and task description. Provide specific file modifications with clear instructions."},
                    {"role": "user",
                     "content": f"Context:\n{context}\n\nTask Description: {task_description}\n\nPlease provide specific file modifications to complete this task. Format your response as a list of file paths and their corresponding changes."}
                ],
                "max_tokens": 2000
            }
        )

        if 'error' in response:
            raise Exception(response['error'])

        # Parse LLM response and apply changes
        modifications = parse_llm_response(response['response'])
        apply_modifications(file_manager, modifications)

        print("Task completed successfully. Files have been modified according to the LLM suggestions.")
    except Exception as e:
        logger.error(f"Failed to execute task: {str(e)}", exc_info=True)
        print(f"Error: Failed to execute task: {str(e)}")


def build_context(file_manager: FileManager, relevant_files: List[str]) -> str:
    context = "Relevant Project Files:\n"
    context += "\n".join(relevant_files)
    context += "\n\nFile Contents:\n"

    for file_path in relevant_files:
        try:
            content = file_manager.read_file(file_path)
            context += f'\n\n#File {file_path}:\n{content}'
        except Exception as e:
            logger.warning(f"Could not read file {file_path}: {str(e)}")

    return context


def apply_modifications(file_manager: FileManager, modifications: Dict[str, str]):
    for file_path, new_content in modifications.items():
        file_manager.write_file(file_path, new_content)


import re
import logging

logger = logging.getLogger(__name__)


def parse_llm_response(response: str) -> Dict[str, str]:
    modifications = {}
    current_file = None
    current_content = []
    file_pattern = re.compile(r'^File:\s*([\w\-./]+)')

    lines = response.split('\n')
    for i, line in enumerate(lines):
        file_match = file_pattern.match(line)
        if file_match:
            if current_file:
                modifications[current_file] = '\n'.join(current_content).strip()
            current_file = file_match.group(1)
            current_content = []
        elif line.strip() == "```" or line.strip() == "```python":
            # Start of a code block
            code_block = []
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == "```":
                    break
                code_block.append(lines[j])
            current_content.extend(code_block)
            i = j  # Skip to the end of the code block
        elif current_file:
            current_content.append(line)

    if current_file:
        modifications[current_file] = '\n'.join(current_content).strip()

    if not modifications:
        logger.warning("No file modifications found in the LLM response.")

    for file, content in modifications.items():
        logger.info(f"Parsed modifications for file: {file}")
        logger.debug(f"Content:\n{content}")

    return modifications


def apply_modifications(file_manager, modifications):
    for file_path, new_content in modifications.items():
        file_manager.write_file(file_path, new_content)

def execute_analyze():
    if not check_autocoder_dir():
        logger.error("Autocoder is not initialized in this directory.")
        print(
            "Autocoder is not initialized in this directory. Please run 'autocoder init' first."
        )
        return

    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
    if not api_key:
        logger.error("No API key found. Cannot proceed with analysis.")
        print(
            "Error: No API key found. Please set ANTHROPIC_API_KEY or CLAUDE_API_KEY in your environment or .env file."
        )
        return

    try:
        workflow = LangGraphWorkflow(api_key)
        print("Analyzing project...")
        result = workflow.execute_analysis({"project_root": os.getcwd()})
        if result != "Analysis completed.":
            print(result)
    except Exception as e:
        logger.error(f"Failed to execute analysis: {str(e)}")
        print(f"Error: Failed to execute analysis: {str(e)}")

def create_files_list():
    if not check_autocoder_dir():
        logger.error("Autocoder is not initialized in this directory.")
        print("Autocoder is not initialized in this directory. Please run 'autocoder init' first.")
        return

    try:
        project_root = os.getcwd()
        autocoder_dir = os.path.join(project_root, ".autocoder")
        files_list_path = os.path.join(autocoder_dir, "files.txt")

        load_dotenv()
        api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('CLAUDE_API_KEY')
        if not api_key:
            logger.error("No API key found. Cannot proceed with task execution.")
            print(
                "Error: No API key found. Please set ANTHROPIC_API_KEY or CLAUDE_API_KEY in your environment or .env file.")
            return

        claude_api = ClaudeAPIWrapper(api_key)
        file_lister = FileListingNode(claude_api)

        result = file_lister.process(project_root)

        if 'error' in result:
            raise Exception(result['error'])

        project_files = result['project_files']

        with open(files_list_path, 'w') as f:
            f.write("\n".join(project_files))

        logger.info(f"Files list created successfully at {files_list_path}")
        print(f"Files list created successfully at {files_list_path}")
    except Exception as e:
        logger.error(f"Failed to create files list: {str(e)}")
        print(f"Error: Failed to create files list: {str(e)}")


def create_context_file():
    if not check_autocoder_dir():
        logger.error("Autocoder is not initialized in this directory.")
        print("Autocoder is not initialized in this directory. Please run 'autocoder init' first.")
        return

    try:
        project_root = os.getcwd()
        autocoder_dir = os.path.join(project_root, ".autocoder")
        context_file_path = os.path.join(autocoder_dir, "context.txt")

        # Use the existing FileListingNode to get the context
        load_dotenv()
        api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('CLAUDE_API_KEY')
        if not api_key:
            logger.error("No API key found. Cannot proceed with task execution.")
            print(
                "Error: No API key found. Please set ANTHROPIC_API_KEY or CLAUDE_API_KEY in your environment or .env file.")
            return


        claude_api = ClaudeAPIWrapper(api_key)
        file_lister = FileListingNode(claude_api)
        result = file_lister.process(project_root)

        if 'error' in result:
            raise Exception(result['error'])

        context = result['context']

        # Write the context to file in chunks to handle potentially large files
        with open(context_file_path, 'w') as f:
            for i in range(0, len(context), 1024 * 1024):  # Write in 1MB chunks
                f.write(context[i:i + 1024 * 1024])

        logger.info(f"Context file created successfully at {context_file_path}")
        print(f"Context file created successfully at {context_file_path}")
        print(f"Total files processed: {len(result['project_files'])}")
        print(f"Context size: {len(context)} bytes")
        print("Files included in context:")
        for file in result['project_files']:
            print(f"  - {file}")
        print("\nExcluded patterns:")
        for pattern in result['excluded_files']:
            print(f"  - {pattern}")
    except Exception as e:
        logger.error(f"Failed to create context file: {str(e)}", exc_info=True)
        print(f"Error: Failed to create context file: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Claude Automated Coding")
    parser.add_argument(
        "command",
        nargs="?",
        default="help",
        choices=["init", "task", "analyze", "create:files-list", "create:context-file", "help"],
        help="Command to execute",
    )
    parser.add_argument(
        "task_description",
        nargs="?",
        default="",
        help="The task description for the automated coding process",
    )
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
    elif args.command == "analyze":
        logger.info("Analyzing project...")
        # Implement analyze functionality
    elif args.command == "create:files-list":
        logger.info("Creating files list...")
        # Implement create:files-list functionality
    elif args.command == "create:context-file":
        logger.info("Creating context file...")
        # Implement create:context-file functionality
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
