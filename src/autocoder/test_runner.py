import subprocess
import os

class TestRunner:
    def __init__(self, project_directory):
        self.project_directory = project_directory

    def run_tests(self):
        try:
            # Change to the project directory
            os.chdir(self.project_directory)

            # Run pytest
            result = subprocess.run(['pytest'], capture_output=True, text=True)

            # Check if tests passed
            if result.returncode == 0:
                return True, "All tests passed"
            else:
                # If tests failed, return the error output
                return False, result.stderr

        except Exception as e:
            return False, f"Error running tests: {str(e)}"

        finally:
            # Change back to the original directory
            os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
