from abc import ABC, abstractmethod
import inspect
import os
from pathlib import Path
from typing import Any, List
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage
from langchain.prompts import load_prompt
from utils import setup_logger
from langchain_openai.chat_models import ChatOpenAI

logger = setup_logger(
    f"{os.getenv('PROJECT_NAME', 'root')}.{Path(__file__).parent.name}"
)


class InputNode(ABC):
    @abstractmethod
    def validate_and_parse(self, state: Any) -> Any:
        """Validate and parse input state"""
        pass


class ProcessNode(ABC):
    """
    Base class for general-purpose nodes in a campaign planning system.

    This abstract class provides core functionality for loading prompts and
    handling message processing. It can be extended for various types of nodes
    in the campaign planning pipeline.

    Attributes:
        llm (ChatOpenAI): Language model instance for generating responses
        prompt (str): Loaded prompt template from YAML file
    """

    def __init__(self, config: dict, prompt_file_name: str = "prompt.yaml") -> None:
        """
        Initialize the base node.
        Args:
            config (dict): Configuration dictionary containing LLM settings
            prompt_file_name (str, optional): Name of the prompt template file.
                Defaults to "prompt.yaml"
        Raises:
            FileNotFoundError: If the prompt file cannot be found
        """
        module_path = Path(inspect.getmodule(self.__class__).__file__)
        prompt_file_path = module_path.parent / prompt_file_name

        if not prompt_file_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file_path}")

        self.llm = ChatOpenAI(
            model=config["LLM"]["MODEL_NAME"],
            temperature=config["LLM"]["TEMPERATURE"],
            max_completion_tokens=config["LLM"]["TOP_P"],
            streaming=config["LLM"]["STREAMING"],
        )
        self.prompt = self._load_prompt(prompt_file_path)

    @staticmethod
    def _load_prompt(prompt_file: Path) -> str:
        """
        Load prompts from a YAML file.

        Args:
            prompt_file (Path): Path to the YAML prompt file

        Returns:
            str: Loaded prompt template

        Raises:
            FileNotFoundError: If the YAML file doesn't exist
        """
        try:
            return load_prompt(prompt_file)
        except FileNotFoundError as e:
            logger.error(f"The prompt YAML file '{prompt_file}' was not found.")
            raise e

    @abstractmethod
    def process(self, state: Any) -> Any:
        """
        Abstract method to invoke the node's processing logic.

        Args:
            state (Any): The state to be processed

        Returns:
            Any: The node's processed response

        Raises:
            NotImplementedError: Must be implemented in a subclass
        """
        raise NotImplementedError("This method must be implemented in a subclass.")

    @staticmethod
    def _to_string(messages: List[AnyMessage]) -> str:
        """
        Flatten a list of messages to a formatted string.

        Args:
            messages (List[AnyMessage]): List of messages (Human, AI, Tool Messages)

        Returns:
            str: Formatted string containing all messages in a conversation format
        """
        response: str = ""
        for message in messages:
            if isinstance(message, HumanMessage):
                response += f"Human: {message.content}\n"
            elif isinstance(message, AIMessage):
                response += f"Assistant: {message.content}\n"
                response += "---\n"

        return response.strip()


class OutputNode(ABC):
    @abstractmethod
    def format_output(self, state: Any) -> Any:
        """Format the output state"""
        pass
