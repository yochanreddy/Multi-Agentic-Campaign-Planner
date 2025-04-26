import logging
import warnings
import os
from pathlib import Path
from datetime import datetime
import uuid
import sys

# Constants
DIVIDER_LENGTH = 80  # Fixed length for all dividers
DIVIDER = "=" * DIVIDER_LENGTH
PREFIX_LENGTH = 50  # Approximate length of timestamp + logger name + level

# ANSI color codes for terminal output
class LogColors:
    GREY = "\033[38;5;240m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    BOLD_RED = "\033[31;1m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    RESET = "\033[0m"

# Agent-specific colors
AGENT_COLORS = {
    "prompt_generator": LogColors.CYAN,
    "image_generator": LogColors.BLUE,
    "image_analyzer": LogColors.MAGENTA,
    "mask_generator": LogColors.YELLOW,
    "cta_generator": LogColors.GREEN,
    "text_layering": LogColors.GREY
}

class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors based on agent and log level"""
    
    def format(self, record):
        # Get agent name from logger name
        agent_name = record.name.split('.')[-1]
        agent_color = AGENT_COLORS.get(agent_name, LogColors.RESET)
        
        # Add color based on log level
        if record.levelno == logging.DEBUG:
            color = LogColors.GREY
        elif record.levelno == logging.INFO:
            color = LogColors.GREEN
        elif record.levelno == logging.WARNING:
            color = LogColors.YELLOW
        elif record.levelno == logging.ERROR:
            color = LogColors.RED
        elif record.levelno == logging.CRITICAL:
            color = LogColors.BOLD_RED
        else:
            color = LogColors.RESET
            
        # Format the message with agent and level colors
        record.msg = f"{agent_color}[{agent_name}]{LogColors.RESET} {color}{record.msg}{LogColors.RESET}"
        return super().format(record)

# Global variables to store session info
LOG_FILE = None

def is_reloader_process():
    """Check if we're in the reloader process"""
    return "uvicorn.reload" in sys.modules

def configure_logging():
    """Configure logging to prevent duplicate logs and write only to file"""
    global LOG_FILE
    
    # If logging is already configured or we're in the reloader process, return
    if LOG_FILE is not None or is_reloader_process():
        return
    
    # Suppress all warnings
    warnings.filterwarnings('ignore')
    
    # Get log level from environment variable and clean it
    log_level = os.getenv("LOG_LEVEL", "INFO").upper().split('#')[0].strip()
    
    # Validate log level
    valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
    if log_level not in valid_levels:
        log_level = 'INFO'  # Default to INFO if invalid
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs/creative_agent")
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Create file handler with fixed name
    LOG_FILE = logs_dir / "creative_planner.log"
    
    # Check if file already exists and remove it
    if LOG_FILE.exists():
        LOG_FILE.unlink()
    
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(log_level)
    
    # Create a custom formatter that ensures consistent divider lengths and alignment
    class ConsistentFormatter(logging.Formatter):
        def format(self, record):
            # Format the timestamp
            record.asctime = self.formatTime(record)
            
            # Replace any divider-like patterns with the fixed-length divider
            if isinstance(record.msg, str):
                if record.msg.strip().startswith('='):
                    # Calculate the prefix length for this specific record
                    prefix = f"{record.asctime} - {record.name} - {record.levelname}"
                    padding = max(0, PREFIX_LENGTH - len(prefix))
                    record.msg = " " * padding + DIVIDER
            
            return super().format(record)
    
    file_handler.setFormatter(ConsistentFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Create stream handler for terminal output
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Configure root logger to prevent propagation and remove all handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)  # Set root logger to WARNING to prevent propagation
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Configure specific agent loggers in order
    agent_loggers = [
        "creative_planner.agents.prompt_generator",
        "creative_planner.agents.image_generator",
        "creative_planner.agents.image_analyzer",
        "creative_planner.agents.mask_generator",
        "creative_planner.agents.cta_generator",
        "creative_planner.agents.text_layering"
    ]
    
    # Configure all loggers to prevent propagation and add both handlers
    for agent_logger in agent_loggers:
        logger = logging.getLogger(agent_logger)
        logger.setLevel(log_level)
        logger.propagate = False  # Prevent propagation to parent loggers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
    
    # Suppress specific loggers
    logging.getLogger("langchain_core.prompts.loading").setLevel(logging.ERROR)
    logging.getLogger("huggingface_hub.file_download").setLevel(logging.ERROR)
    logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.ERROR)
    logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
    logging.getLogger("uvicorn.access").setLevel(logging.ERROR)
    logging.getLogger("uvicorn.reload").setLevel(logging.ERROR)
    logging.getLogger("watchfiles.main").setLevel(logging.ERROR)
    
    # Configure httpx logger for creative planner only
    httpx_logger = logging.getLogger("httpx")
    httpx_logger.setLevel(logging.ERROR)  # Set to ERROR to reduce noise
    httpx_logger.propagate = False
    for handler in httpx_logger.handlers[:]:
        httpx_logger.removeHandler(handler)
    
    # Add a filter to only log httpx messages from creative planner
    class CreativePlannerFilter(logging.Filter):
        def filter(self, record):
            # Only log httpx messages that are part of creative planner operations
            return "creative_planner" in record.name.lower()
    
    httpx_logger.addFilter(CreativePlannerFilter())
    httpx_logger.addHandler(file_handler) 