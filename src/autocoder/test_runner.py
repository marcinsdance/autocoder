import subprocess
import os

class TestRunner:
    def __init__(self):
        pass

    def run_tests(self):
        try:
            # Run pytest in the current directory
            result = subprocess.run(['pytest'], capture_output=True, text=True)

            # Check if tests passed
            if result.returncode == 0:
                return True, "All tests passed"
            else:
                # If tests failed, return the error output
                return False, result.stderr

        except Exception as e:
            return False, f"Error running tests: {str(e)}"
