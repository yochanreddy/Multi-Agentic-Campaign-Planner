import logging
import warnings
import os

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

def configure_logging():
    """Configure logging to prevent duplicate logs and add colors"""
    # Suppress all warnings
    warnings.filterwarnings('ignore')
    
    # Get log level from environment variable and clean it
    log_level = os.getenv("LOG_LEVEL", "INFO").upper().split('#')[0].strip()
    
    # Validate log level
    valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
    if log_level not in valid_levels:
        log_level = 'INFO'  # Default to INFO if invalid
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove all existing handlers to prevent duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create a single console handler with colored formatter
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Suppress specific loggers
    logging.getLogger("langchain_core.prompts.loading").setLevel(logging.ERROR)
    logging.getLogger("huggingface_hub.file_download").setLevel(logging.ERROR)
    logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.ERROR)
    logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
    logging.getLogger("uvicorn.access").setLevel(logging.ERROR)
    logging.getLogger("uvicorn.reload").setLevel(logging.ERROR)
    logging.getLogger("watchfiles.main").setLevel(logging.ERROR) 