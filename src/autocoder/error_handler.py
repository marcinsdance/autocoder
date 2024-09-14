import traceback
import logging
from typing import Union, Dict, Any

logger = logging.getLogger(__name__)

class ErrorHandler:
    @staticmethod
    def handle_error(error: Union[str, Exception], context: Dict[str, Any] = None) -> Dict[str, Any]:
        if isinstance(error, str):
            error_message = error
        else:
            error_message = str(error)

        logger.error(f"An error occurred: {error_message}")

        error_report = {
            "error_message": error_message,
            "traceback": ErrorHandler.get_traceback(error),
            "context": context or {},
            "suggestions": ErrorHandler.get_suggestions(error_message)
        }

        return error_report

    @staticmethod
    def get_traceback(error: Union[str, Exception]) -> str:
        if isinstance(error, Exception):
            return "".join(traceback.format_exception(type(error), error, error.__traceback__))
        return "No traceback available for string errors."

    @staticmethod
    def get_suggestions(error_message: str) -> list:
        # This method can be expanded with more specific suggestions based on error types
        suggestions = [
            "Check the error message and traceback for details on where the error occurred.",
            "Review any recent changes to the affected components.",
            "Ensure all necessary dependencies are installed and up to date.",
            "If the error persists, consider reverting recent changes or seeking further assistance."
        ]
        return suggestions

    @staticmethod
    def log_error(error: Union[str, Exception], context: Dict[str, Any] = None):
        error_report = ErrorHandler.handle_error(error, context)
        logger.error(f"Error Report: {error_report}")

    @staticmethod
    def wrap_node(node_func):
        def wrapped_node(state: Dict[str, Any]) -> Dict[str, Any]:
            try:
                return node_func(state)
            except Exception as e:
                error_report = ErrorHandler.handle_error(e, context={"node": node_func.__name__, "state": state})
                state["error"] = error_report
                return state
        return wrapped_node
