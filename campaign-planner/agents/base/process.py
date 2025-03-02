from abc import ABC, abstractmethod
import inspect
from pathlib import Path
from typing import Any, List
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage
from langchain.prompts import load_prompt, PromptTemplate
from utils import get_module_logger, Generator
from langchain_core.runnables.config import RunnableConfig

logger = get_module_logger()


class BaseProcessNode(ABC):
    """
    Base class for general-purpose nodes in a campaign planning system.

    This abstract class provides core functionality for loading prompts and
    handling message processing. It can be extended for various types of nodes
    in the campaign planning pipeline.

    The class handles:
    - Loading and managing prompt templates from YAML files
    - Interfacing with language models
    - Processing conversation messages

    Attributes:
        llm (ChatOpenAI): Language model instance for generating responses
        prompt (str): Loaded prompt template from YAML file
    """

    def __init__(
        self, config: dict, model_name: str, prompt_file_name: str = "prompt.yaml"
    ) -> None:
        """
        Initialize the base node with configuration and prompt template.

        Args:
            config (dict): Configuration dictionary containing LLM settings and parameters
            model_name (str): Name of the language model to use
            prompt_file_name (str, optional): Name of the prompt template file.
                Defaults to "prompt.yaml"

        Raises:
            FileNotFoundError: If the specified prompt template file cannot be found
        """
        module_path = Path(inspect.getmodule(self.__class__).__file__)
        prompt_file_path = module_path.parent / prompt_file_name

        if not prompt_file_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file_path}")

        self.llm = Generator(config).get_model(name=model_name)
        self.prompt = self._load_prompt(prompt_file_path)

    @staticmethod
    def _load_prompt(prompt_file: Path) -> PromptTemplate:
        """
        Load and parse prompts from a YAML file.

        Args:
            prompt_file (Path): Path to the YAML prompt template file

        Returns:
            PromptTemplate: Loaded and parsed prompt template

        Raises:
            FileNotFoundError: If the specified YAML file doesn't exist
            YAMLError: If the YAML file is malformed or cannot be parsed
        """
        try:
            return load_prompt(prompt_file)
        except FileNotFoundError as e:
            logger.error(f"The prompt YAML file '{prompt_file}' was not found.")
            raise e

    @abstractmethod
    def process(self, state: Any, config: RunnableConfig) -> Any:
        """
        Abstract method to invoke the node's processing logic.

        This method should be implemented by subclasses to define the specific
        processing logic for each type of node in the campaign planning system.

        Args:
            state (Any): The input state to be processed

        Returns:
            Any: The processed response or transformed state

        Raises:
            NotImplementedError: Must be implemented in a subclass
        """
        raise NotImplementedError("This method must be implemented in a subclass.")

    @staticmethod
    def _to_string(messages: List[AnyMessage]) -> str:
        """
        Flatten a list of conversation messages to a formatted string.

        Converts a list of different message types (Human, AI, Tool) into a
        human-readable conversation format with clear separation between messages.

        Args:
            messages (List[AnyMessage]): List of conversation messages
                (Human, AI, Tool Messages)

        Returns:
            str: Formatted string containing all messages in a conversation format,
                with speakers clearly identified and messages separated by
                delimiting markers
        """
        response: str = ""
        for message in messages:
            if isinstance(message, HumanMessage):
                response += f"Human: {message.content}\n"
            elif isinstance(message, AIMessage):
                response += f"Assistant: {message.content}\n"
                response += "---\n"

        return response.strip()
