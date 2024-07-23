import subprocess
import os
import shutil

class TestRunner:
    def __init__(self, project_directory):
        self.project_directory = project_directory

    def run_tests(self):
        try:
            # Check if pytest is available
            if not self._is_pytest_installed():
                return False, "pytest is not installed. Please install it using 'pip install pytest' and try again."

            # Change to the project directory
            os.chdir(self.project_directory)

            # Run pytest
            result = subprocess.run(['pytest'], capture_output=True, text=True)

            # Change back to the original directory
            os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

            # Check if tests passed
            if result.returncode == 0:
                return True, "All tests passed"
            else:
                # If tests failed, return the error output
                return False, result.stderr

        except Exception as e:
            return False, f"Error running tests: {str(e)}"

    def _is_pytest_installed(self):
        return shutil.which('pytest') is not None
