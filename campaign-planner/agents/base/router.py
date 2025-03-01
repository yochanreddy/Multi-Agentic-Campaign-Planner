from abc import ABC, abstractmethod
from typing import Any
from langchain_core.runnables.config import RunnableConfig
from utils import get_module_logger

logger = get_module_logger()


class RouterNode(ABC):
    @abstractmethod
    def determine_next_step(self, state: Any, config: RunnableConfig) -> Any:
        """
        Evaluates the current state and determines the next action or path.

        Args:
            state (Any): Current state to be evaluated
            config (RunnableConfig): Configuration parameters for the decision process

        Returns:
            Any: Next step or action to be taken

        Raises:
            NotImplementedError: Must be implemented in a subclass
        """
        pass
