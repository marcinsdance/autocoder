import os
import logging

logger = logging.getLogger(__name__)

def check_autocoder_dir():
    autocoder_dir = os.path.join(os.getcwd(), ".autocoder")
    dir_exists = os.path.isdir(autocoder_dir)
    logger.info(f".autocoder directory {'exists' if dir_exists else 'does not exist'}")
    return dir_exists

def display_init_message():
    message = """
Autocoder isn't initialized in this location. Please run "autocoder init" command for the autocoder to start working on files in this location.

Usage: autocoder [command]
The available commands for execution are listed below.
Commands:
  init          Init autocoder in this directory
  task          Execute a task in an initialized directory
  help          Display help information
"""
    print(message)

def init_autocoder():
    autocoder_dir = os.path.join(os.getcwd(), ".autocoder")
    project_state_file = os.path.join(autocoder_dir, "project_state.txt")

    if not os.path.exists(autocoder_dir):
        os.makedirs(autocoder_dir)
        with open(project_state_file, 'w') as f:
            f.write('initialized')
        logger.info("Autocoder initialized successfully in this directory with project state 'initialized'.")
        print("Autocoder initialized successfully in this directory with project state 'initialized'.")
    else:
        logger.info("Autocoder is already initialized in this directory.")
        print("Autocoder is already initialized in this directory.")
