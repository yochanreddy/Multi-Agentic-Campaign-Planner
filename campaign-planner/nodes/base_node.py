from abc import ABC, abstractmethod
import inspect
from pathlib import Path
from typing import Any, List
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage
from langchain.prompts import load_prompt
from utils import setup_logger
from langchain_openai.chat_models import ChatOpenAI

logger = setup_logger("campaign_planner")


class BaseNode(ABC):
    """
    Base class for general-purpose nodes.
    This abstract class can be extended for various types of nodes.
    """

    def __init__(self, config: dict, prompt_file_name: str = "prompt.yaml") -> None:
        # look in the same directory as the subclass module
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
        """Loads prompts from a YAML file."""
        try:
            return load_prompt(prompt_file)  # Load prompt using the resolved path
        except FileNotFoundError as e:
            logger.error(f"The prompt YAML file '{prompt_file}' was not found.")
            raise e

    @abstractmethod
    def __call__(self, state: Any) -> Any:
        """
        Abstract method to invoke the node.

        Args:
            state (Any): The state to be processed.

        Returns:
            Any: The node's response.

        Raises:
            NotImplementedError: Must be implemented in a subclass.
        """
        raise NotImplementedError("This method must be implemented in a subclass.")

    @staticmethod
    def _to_string(messages: List[AnyMessage]) -> str:
        """flatten the messages list to a string format

        Args:
            messages (List[AnyMessage]): Mix of Human, AI, Tool Messages

        Returns:
            str: formatted messages
        """
        response: str = ""
        for message in messages:
            if isinstance(message, HumanMessage):
                response += f"Human: {message.content}"
            elif isinstance(message, AIMessage):
                response += f"Assistant: {message.content}"
                response += "\n---\n"

        return response  # Added return statement that was missing in original
