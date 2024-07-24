import argparse
import logging
from pathlib import Path
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

def run_automated_coding(task_description):
    # Initialize configuration
    config = Config()
    project_dir = config.get_project_directory()
    logger.info(f"Using project directory: {project_dir}")

    # Initialize components
    file_manager = FileManager(project_dir)
    context_builder = ContextBuilder()
    task_interpreter = TaskInterpreter()
    code_modifier = CodeModifier()
    test_runner = TestRunner(project_dir)  # Pass project_dir here
    error_handler = ErrorHandler()
    claude_api = ClaudeAPIWrapper(config.get_api_key())

    # Initialize LangGraph workflow
    workflow = LangGraphWorkflow(
        file_manager, context_builder, task_interpreter,
        code_modifier, test_runner, error_handler, claude_api
    )

    # Execute workflow
    result = workflow.execute(task_description)

    print(f"Task completed. Result: {result}")


def analyze_project():
    config = Config()
    project_dir = Path.cwd()
    file_manager = FileManager(project_dir)

    # Initialize other components
    context_builder = ContextBuilder()
    task_interpreter = TaskInterpreter()
    code_modifier = CodeModifier()
    test_runner = TestRunner(project_dir)
    error_handler = ErrorHandler()
    claude_api = ClaudeAPIWrapper(config.get_api_key())

    workflow = LangGraphWorkflow(
        file_manager, context_builder, task_interpreter,
        code_modifier, test_runner, error_handler, claude_api
    )
    workflow.analyze_project()


def main():
    parser = argparse.ArgumentParser(description="Claude Automated Coding")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze the current project")

    # Coding task command
    task_parser = subparsers.add_parser("code", help="Perform an automated coding task")
    task_parser.add_argument("task", help="The task description for the automated coding process")

    args = parser.parse_args()

    if args.command == "analyze":
        analyze_project()
    elif args.command == "code":
        run_automated_coding(args.task)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
