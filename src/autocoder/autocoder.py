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
    test_runner = TestRunner()
    error_handler = ErrorHandler()
    claude_api = ClaudeAPIWrapper(config.get_api_key())  # Updated to use get_api_key()

    # Initialize LangGraph workflow
    workflow = LangGraphWorkflow(
        file_manager, context_builder, task_interpreter,
        code_modifier, test_runner, error_handler, claude_api
    )

    # Execute workflow
    result = workflow.execute(task_description)

    print(f"Task completed. Result: {result}")

def main():
    parser = argparse.ArgumentParser(description="Claude Automated Coding")
    parser.add_argument("task", help="The task description for the automated coding process")
    args = parser.parse_args()

    run_automated_coding(args.task)

if __name__ == "__main__":
    main()
