import logging
import os
import sys

# Dynamically set the log directory to the script's current location
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
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

        # File handler (for saving logs)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')  # <-- Force UTF-8 here
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(file_handler)

        # Console handler (optional, for printing to terminal)
        try:
            sys.stdout.reconfigure(encoding='utf-8')  # <-- Ensure stdout supports UTF-8
        except AttributeError:
            # For older Python versions (<3.7), manually wrap
            sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(console_handler)

        logger.propagate = False  # Prevent duplicate logs from root logger

    return logger

