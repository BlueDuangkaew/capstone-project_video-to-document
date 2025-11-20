from loguru import logger
import os

def setup_logger(log_path="output/logs/app.log"):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logger.add(log_path, rotation="5 MB")
    return logger

log = setup_logger()
