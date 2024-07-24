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
        self.project_analyzer = ProjectAnalyzer(file_manager)

    def execute(self, task_description):
        try:
            # Interpret the task
            interpreted_task = self.task_interpreter.interpret_task(task_description)
            logger.info(f"Task interpreted: {interpreted_task['task_type']}")

            # Build context
            context = self.context_builder.build_context(self.file_manager)
            logger.info("Context built successfully")

            # Generate prompt for Claude
            task_prompt = self.task_interpreter.get_prompt_for_task(interpreted_task)
            full_prompt = f"Context:\n{context}\n\nTask:\n{task_prompt}\n\nPlease provide the necessary code changes or additions to complete this task."

            # Get response from Claude
            modifications = self.claude_api.generate_response(full_prompt)
            logger.info("Received response from Claude API")

            if modifications is None:
                return "Error: Failed to generate response from Claude API"

            # Apply modifications
            for file in interpreted_task['affected_files']:
                if self.file_manager.file_exists(file):
                    original_code = self.file_manager.read_file(file)
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

    def analyze_project(self):
        logger.info("Starting project analysis...")
        project_analysis = self.project_analyzer.analyze_project()
        if project_analysis:
            logger.info("Project analysis complete.")
            logger.info(f"Root directory: {project_analysis['root_directory']}")
            logger.info("Project structure:")
            self._print_structure(project_analysis['project_structure'])
            logger.info("\nFile list:")
            for file in project_analysis['file_list']:
                logger.info(file)
            logger.info("\nFile contents:")
            for file, content in project_analysis['file_contents'].items():
                logger.info(f"\n#File {file}:")
                logger.info(content[:500] + "..." if len(content) > 500 else content)
        else:
            logger.error("Project analysis failed.")

    def _print_structure(self, structure, indent=""):
        for key, value in structure.items():
            if value is None:
                logger.info(f"{indent}{key}")
            else:
                logger.info(f"{indent}{key}/")
                self._print_structure(value, indent + "  ")
