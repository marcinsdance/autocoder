import os
import logging

logger = logging.getLogger(__name__)

def check_autocoder_dir(state):
    autocoder_dir = os.path.join(os.getcwd(), ".autocoder")
    dir_exists = os.path.isdir(autocoder_dir)
    logger.info(f".autocoder directory {'exists' if dir_exists else 'does not exist'}")
    return {"autocoder_dir_exists": dir_exists}
