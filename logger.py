import logging
import os

# Ensure log directory exists
LOG_DIR = "/Users/satyamanand/Downloads/Data/Satyam/Temp/instahyre"
os.makedirs(LOG_DIR, exist_ok=True)


def get_logger(name):
    """
    Creates and returns a logger instance with a unique log file per bot.

    :param name: Name of the bot (e.g., 'instahyre' or 'naukri')
    :return: Logger instance
    """
    logger = logging.getLogger(name)

    # Prevent duplicate handlers
    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)

        # Define log file path
        log_file = os.path.join(LOG_DIR, f"{name}.log")

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(file_handler)

        # Console handler (optional)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(console_handler)

        logger.propagate = False  # Prevent duplicate logs from root logger

    return logger
