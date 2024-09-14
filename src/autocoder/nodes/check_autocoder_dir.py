from ..state import State
from ..nodes.tools.directory_checker import check_autocoder_dir as check_dir
from ..error_handler import ErrorHandler

@ErrorHandler.wrap_node
def check_autocoder_dir(state: State) -> State:
    state["autocoder_dir_exists"] = check_dir()
    return state
