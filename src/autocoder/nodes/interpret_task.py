from ..state import State
from ..task_interpreter import TaskInterpreter

def interpret_task(state: State) -> State:
    task_interpreter = TaskInterpreter()
    interpreted_task = task_interpreter.interpret_task(state["messages"][-1].content)
    state["interpreted_task"] = interpreted_task
    return state
