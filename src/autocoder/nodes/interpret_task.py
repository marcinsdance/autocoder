from ..state import State
from ..task_interpreter import TaskInterpreter
from ..error_handler import ErrorHandler

@ErrorHandler.wrap_node
def interpret_task(state: State) -> State:
    task_interpreter = TaskInterpreter()
    task_description = state["messages"][-1].content
    interpreted_task = task_interpreter.interpret_task(task_description)
    state["interpreted_task"] = interpreted_task
    return state
