from ..state import State
from ..context_builder import ContextBuilder
from ..file_manager import FileManager
from ..error_handler import ErrorHandler

@ErrorHandler.wrap_node
def build_context(state: State) -> State:
    file_manager = FileManager(state["project_root"])
    context_builder = ContextBuilder()

    files = file_manager.get_file_contents()
    context = context_builder.build_context(files)

    state["files"] = files
    state["context"] = context

    return state
