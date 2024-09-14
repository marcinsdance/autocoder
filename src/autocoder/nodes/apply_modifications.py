from ..state import State
from ..code_modifier import CodeModifier
from ..file_manager import FileManager

def apply_modifications(state: State) -> State:
    code_modifier = CodeModifier()
    file_manager = FileManager(state["project_root"])

    for file in state["interpreted_task"]["affected_files"]:
        if file in state["files"]:
            original_code = state["files"][file]
            modified_code = code_modifier.modify_code(original_code, state["modifications"])
            file_manager.write_file(file, modified_code)
            state["files"][file] = modified_code

    return state
