# logger.py - Place this in a common location all scripts can access
import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


# ANSI color codes for terminal output
class LogColors:
    GREY = "\033[38;5;240m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    BOLD_RED = "\033[31;1m"
    RESET = "\033[0m"


class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors based on log level"""

    FORMATS = {
        logging.DEBUG: LogColors.GREY
        + "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        + LogColors.RESET,
        logging.INFO: LogColors.GREEN
        + "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        + LogColors.RESET,
        logging.WARNING: LogColors.YELLOW
        + "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        + LogColors.RESET,
        logging.ERROR: LogColors.RED
        + "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        + LogColors.RESET,
        logging.CRITICAL: LogColors.BOLD_RED
        + "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        + LogColors.RESET,
    }

    def format(self, record):
        log_format = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_format)
        return formatter.format(record)


def setup_logger(logger_name: str, log_dir: str = "logs"):
    """
    Set up a logger with the following features:
    - Log level from environment variable LOG_LEVEL (default: INFO)
    - Color-coded log levels for console output
    - Daily log rotation at midnight
    - Prevents duplicate handlers

    Args:
        logger_name (str): Name of the logger
        log_dir (str): Directory to store log files

    Returns:
        logging.Logger: Configured logger
    """
    # Get logger and prevent duplicate handlers
    logger = logging.getLogger(logger_name)

    # If logger already has handlers, assume it's configured and return it
    if logger.handlers:
        return logger

    # Get log level from environment variable (default to INFO)
    log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    # Set the log level
    logger.setLevel(log_level)

    # Create log directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Set up file handler with rotation at midnight
    log_file = log_path / f"{logger_name}.log"
    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when="midnight",
        interval=1,
        backupCount=30,  # Keep logs for 30 days
        encoding="utf-8",
    )

    # Plain formatter for file output
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    # Set up console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter())

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Logger initialized with level {log_level_name}")

    return logger
