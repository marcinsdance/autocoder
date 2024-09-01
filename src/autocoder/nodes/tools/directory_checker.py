import os
import logging

logger = logging.getLogger(__name__)


def check_autocoder_dir(state):
    autocoder_dir = os.path.join(os.getcwd(), ".autocoder")
    dir_exists = os.path.isdir(autocoder_dir)
    logger.info(f".autocoder directory {'exists' if dir_exists else 'does not exist'}")

    if not dir_exists:
        display_init_message()

    return {"autocoder_dir_exists": dir_exists}


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
