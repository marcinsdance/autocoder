import logging

logger = logging.getLogger(__name__)


class LangGraphWorkflow:
    def __init__(self, file_manager, context_builder, task_interpreter,
                 code_modifier, test_runner, error_handler, claude_api):
        self.file_manager = file_manager
        self.context_builder = context_builder
        self.task_interpreter = task_interpreter
        self.code_modifier = code_modifier
        self.test_runner = test_runner
        self.error_handler = error_handler
        self.claude_api = claude_api

    def execute(self, task_description):
        try:
            # Interpret the task
            interpreted_task = self.task_interpreter.interpret_task(task_description)
            logger.info(f"Task interpreted: {interpreted_task['task_type']}")

            # Build context
            files = self.file_manager.list_files()
            file_contents = {f: self.file_manager.read_file(f) for f in files}
            context = self.context_builder.build_context(file_contents)
            logger.info("Context built successfully")

            # Generate prompt for Claude
            task_prompt = self.task_interpreter.get_prompt_for_task(interpreted_task)
            full_prompt = f"Context:\n{context}\n\nTask:\n{task_prompt}"
            logger.info("Prompt generated for Claude API")

            # Get response from Claude
            modifications = self.claude_api.generate_response(full_prompt)
            logger.info("Received response from Claude API")

            # Apply modifications
            for file in interpreted_task['affected_files']:
                if file in file_contents:
                    original_code = file_contents[file]
                    modified_code = self.code_modifier.modify_code(original_code, modifications)
                    self.file_manager.write_file(file, modified_code)
                    logger.info(f"Modified file: {file}")

            # Run tests
            success, test_result = self.test_runner.run_tests()
            if not success:
                error_report = self.error_handler.handle_error(test_result)
                logger.warning("Tests failed. See error report for details.")
                return error_report

            logger.info("Task completed successfully")
            return f"Task completed successfully. Test results: {test_result}"
        except Exception as e:
            error_report = self.error_handler.handle_error(e)
            self.error_handler.log_error(e)
            return error_report
