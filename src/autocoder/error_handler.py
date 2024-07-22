import traceback
import logging

logger = logging.getLogger(__name__)


class ErrorHandler:
    def __init__(self):
        pass

    def handle_error(self, error):
        if isinstance(error, str):
            # If error is already a string (e.g., from TestRunner)
            error_message = error
        else:
            # If error is an exception
            error_message = str(error)

        logger.error(f"An error occurred: {error_message}")

        # Get the full traceback
        tb = traceback.extract_tb(error.__traceback__) if hasattr(error, '__traceback__') else []

        # Format the error report
        error_report = f"Error: {error_message}\n\n"
        error_report += "Traceback:\n"
        for frame in tb:
            error_report += f"  File '{frame.filename}', line {frame.lineno}, in {frame.name}\n"
            error_report += f"    {frame.line}\n"

        # Provide some general advice
        error_report += "\nSuggestions:\n"
        error_report += "1. Check the traceback above to identify where the error occurred.\n"
        error_report += "2. Review any recent changes to the affected files.\n"
        error_report += "3. Ensure all necessary dependencies are installed and up to date.\n"
        error_report += "4. If the error persists, consider reverting recent changes or seeking further assistance.\n"

        return error_report

    def log_error(self, error):
        logger.error(f"An error occurred: {str(error)}")
        logger.error(traceback.format_exc())
