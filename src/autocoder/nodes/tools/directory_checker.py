import os
import logging

logger = logging.getLogger(__name__)


def check_autocoder_dir():
    autocoder_dir = os.path.join(os.getcwd(), ".autocoder")
    project_state_file = os.path.join(autocoder_dir, "project_state.txt")
    return os.path.isdir(autocoder_dir) and os.path.isfile(project_state_file)


def display_init_message():
    message = """
Autocoder isn't initialized in this location. Please run "autocoder init" command for the autocoder to start working on files in this location.

Usage: autocoder [command]
The available commands for execution are listed below.
Commands:
  init          Init autocoder in this directory
  task          Execute a task in an initialized directory
  analyze       Analyze the project in an initialized directory
  help          Display help information
"""
    print(message)

def display_usage_message():
    message = """
Usage: autocoder [command]
The available commands for execution are listed below.
Commands:
  init                 Init autocoder in this directory
  task                 Execute a task in an initialized directory
  analyze              Analyze the project in an initialized directory
  create:files-list    Create a list of all project files (respects .gitignore)
  create:context-file  Create a context file with the content of all project files
  help                 Display help information
"""
    print(message)


def init_autocoder():
    autocoder_dir = os.path.join(os.getcwd(), ".autocoder")
    project_state_file = os.path.join(autocoder_dir, "project_state.txt")

    if not check_autocoder_dir():
        os.makedirs(autocoder_dir, exist_ok=True)
        with open(project_state_file, 'w') as f:
            f.write('initialized')
        logger.info("Autocoder initialized successfully in this directory with project state 'initialized'.")
        print("Autocoder initialized successfully in this directory with project state 'initialized'.")
    else:
        logger.info("Autocoder is already initialized in this directory.")
        print("Autocoder is already initialized in this directory.")
