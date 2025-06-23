import logging
import os
from typing import Optional, Dict, Any
from openai import OpenAI

def get_required_env_var(name: str, default: Optional[str] = None) -> str:
    """
    Get a required environment variable or use default value if not found.

    Args:
        name (str): Name of the environment variable
        default (Optional[str]): Default value to use if environment variable is not set

    Returns:
        str: Value of the environment variable or default value

    Raises:
        ValueError: If the environment variable is not set and no default is provided
    """
    value = os.getenv(name)
    if value is None:
        if default is None:
            raise ValueError(f"Required environment variable {name} is not set")
        return default
    return value

def get_module_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name (Optional[str]): Name of the module. If None, uses the root logger.

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def ensure_directory_exists(path: str) -> None:
    """
    Ensure that a directory exists, creating it if necessary.

    Args:
        path (str): Path to the directory
    """
    os.makedirs(path, exist_ok=True)

class Generator:
    """Utility class for generating content using OpenAI models"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the generator with configuration.

        Args:
            config (Dict[str, Any]): Configuration dictionary containing model settings
        """
        self.config = config
        self.openai = OpenAI(api_key=get_required_env_var("OPENAI_API_KEY"))

    def get_model(self, name: str = "gpt-4") -> Any:
        """
        Get the configured model instance.

        Args:
            name (str): Name of the model to use

        Returns:
            Any: Configured model instance
        """
        return self.openai 