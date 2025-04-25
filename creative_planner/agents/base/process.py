from abc import ABC, abstractmethod
import inspect
from pathlib import Path
from typing import Any, List, Dict, Optional
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage
from langchain.prompts import load_prompt, PromptTemplate
from creative_planner.utils import get_module_logger, Generator
from langchain_core.runnables.config import RunnableConfig
from langchain_core.runnables import Runnable
from creative_planner.utils.logger import setup_logger
from creative_planner.exceptions.exceptions import NyxAIException
from creative_planner.state import State
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

logger = setup_logger("base_process")


class BaseProcessNode(Runnable, ABC):
    """
    Base class for general-purpose nodes in a creative planning system.

    This abstract class provides core functionality for loading prompts and
    handling message processing. It can be extended for various types of nodes
    in the creative planning pipeline.

    The class handles:
    - Loading and managing prompt templates from YAML files
    - Interfacing with language models
    - Processing conversation messages

    Attributes:
        llm (ChatOpenAI): Language model instance for generating responses
        prompt (str): Loaded prompt template from YAML file
    """

    def __init__(self, config: Dict[str, Any], model_name: str = "gpt-4"):
        """
        Initialize the base node with configuration and prompt template.

        Args:
            config (dict): Configuration dictionary containing LLM settings and parameters
            model_name (str): Name of the language model to use
        """
        super().__init__()
        self.config = config
        self.model_name = model_name
        self.model: Optional[BaseChatModel] = None
        self.processor = None
        self._load_model()

    def _load_model(self):
        """Load the model and processor"""
        try:
            self.MODEL_NAME = self.model_name
            self.processor = None  # No processor needed for GPT-4
            self.model = ChatOpenAI(
                model_name=self.model_name,
                temperature=0.7,
                api_key=self.config.get("openai_api_key")
            )
        except Exception as e:
            logger.exception("Error loading model or processor")
            raise NyxAIException(
                internal_code=7109,
                message="Error loading config or model",
                detail=f"7109: {str(e)}"
            )

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

    async def _invoke_llm(self, prompt: str) -> str:
        """Invoke the language model with the given prompt"""
        try:
            # Create a chain with the prompt template and model
            chain = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful assistant."),
                ("user", "{input}")
            ]) | self.model | StrOutputParser()
            
            # Invoke the chain
            result = await chain.ainvoke({"input": prompt})
            return result
            
        except Exception as e:
            logger.exception("Error invoking LLM")
            raise NyxAIException(
                internal_code=7106,
                message="Error invoking LLM",
                detail=f"7106: {str(e)}"
            )

    @abstractmethod
    async def process(self, state: State, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Abstract method to invoke the node's processing logic.

        This method should be implemented by subclasses to define the specific
        processing logic for each type of node in the creative planning system.

        Args:
            state (State): The input state to be processed

        Returns:
            Dict[str, Any]: The processed response or transformed state

        Raises:
            NotImplementedError: Must be implemented in a subclass
        """
        raise NotImplementedError("This method must be implemented in a subclass.")

    async def invoke(self, input: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Invoke the process with the given input and config"""
        try:
            # Convert input to State
            state = State(**input)
            
            # Process the state
            result = await self.process(state, config or {})
            
            # Ensure we return a dictionary
            if isinstance(result, dict):
                return result
            elif hasattr(result, 'dict'):
                return result.dict()
            else:
                raise ValueError(f"Unexpected return type: {type(result)}")
                
        except Exception as e:
            logger.exception("Error in process invocation")
            raise NyxAIException(
                internal_code=7107,
                message="Error in process invocation",
                detail=f"7107: {str(e)}"
            )

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