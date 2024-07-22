import re
from enum import Enum


class TaskType(Enum):
    ADD_FEATURE = "add_feature"
    FIX_BUG = "fix_bug"
    REFACTOR = "refactor"
    OPTIMIZE = "optimize"
    TEST = "test"
    DOCUMENT = "document"
    UNKNOWN = "unknown"


class TaskInterpreter:
    def __init__(self):
        self.task_type_keywords = {
            TaskType.ADD_FEATURE: ["add", "create", "implement", "new feature"],
            TaskType.FIX_BUG: ["fix", "bug", "issue", "problem", "error"],
            TaskType.REFACTOR: ["refactor", "restructure", "reorganize"],
            TaskType.OPTIMIZE: ["optimize", "improve performance", "speed up"],
            TaskType.TEST: ["test", "unit test", "integration test"],
            TaskType.DOCUMENT: ["document", "add comments", "explain"]
        }

    def interpret_task(self, task_description):
        task_type = self._determine_task_type(task_description)
        affected_files = self._identify_affected_files(task_description)
        subtasks = self._break_into_subtasks(task_description)

        return {
            "original_description": task_description,
            "task_type": task_type.value,
            "affected_files": affected_files,
            "subtasks": subtasks
        }

    def _determine_task_type(self, task_description):
        task_description_lower = task_description.lower()
        for task_type, keywords in self.task_type_keywords.items():
            if any(keyword in task_description_lower for keyword in keywords):
                return task_type
        return TaskType.UNKNOWN

    def _identify_affected_files(self, task_description):
        # Simple regex to find file names (adjust as needed)
        file_pattern = r'\b[\w-]+\.(py|js|html|css|md)\b'
        return list(set(re.findall(file_pattern, task_description)))

    def _break_into_subtasks(self, task_description):
        # Simple subtask breakdown (can be improved with NLP techniques)
        subtasks = task_description.split(". ")
        return [subtask.strip() for subtask in subtasks if subtask.strip()]

    def get_prompt_for_task(self, interpreted_task):
        task_type = interpreted_task['task_type']
        affected_files = ", ".join(interpreted_task['affected_files']) if interpreted_task[
            'affected_files'] else "not specified"

        prompt = f"Task Type: {task_type}\n"
        prompt += f"Affected Files: {affected_files}\n"
        prompt += "Original Description: " + interpreted_task['original_description'] + "\n"
        prompt += "Subtasks:\n"
        for i, subtask in enumerate(interpreted_task['subtasks'], 1):
            prompt += f"{i}. {subtask}\n"

        prompt += "\nBased on this information, please provide a detailed plan to accomplish this task. Include specific code modifications or additions where applicable."

        return prompt
