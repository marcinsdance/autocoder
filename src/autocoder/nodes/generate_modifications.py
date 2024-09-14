from ..state import State
from ..task_interpreter import TaskInterpreter


def generate_modifications(state: State) -> State:
    task_interpreter = TaskInterpreter()
    claude_api = state["claude_api"]

    task_prompt = task_interpreter.get_prompt_for_task(state["interpreted_task"])
    full_prompt = f"Context:\n{state['context']}\n\nTask:\n{task_prompt}"

    modifications = claude_api.generate_response(full_prompt)

    state["modifications"] = modifications

    return state
