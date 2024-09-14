from ..state import State
from ..test_runner import TestRunner


def run_tests(state: State) -> State:
    test_runner = TestRunner()

    success, test_result = test_runner.run_tests()

    state["test_results"] = {
        "success": success,
        "details": test_result
    }

    return state
