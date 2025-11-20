import logging
import os
from datetime import datetime

def setup_logger(base_log_dir):
    os.makedirs(base_log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"run_{timestamp}.log"
    log_path = os.path.join(base_log_dir, log_filename)

    logger = logging.getLogger("video_trimmer")
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(log_path)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Optional: also log to console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.info("Logger initialized.")
    return logger, log_path
