from abc import ABC, abstractmethod
from typing import Any
from langchain_core.runnables.config import RunnableConfig
from creative_planner.utils import get_module_logger

logger = get_module_logger()


class BaseHumanNode(ABC):
    @abstractmethod
    def get_human_validation(self, state: Any, config: RunnableConfig) -> Any:
        """
        Get human validation and parse output state.

        Args:
            state (Any): Raw output state to be validated and parsed
            config (RunnableConfig): Configuration for the runnable

        Returns:
            Any: Human-validated and parsed state ready for processing

        Raises:
            NotImplementedError: Must be implemented in a subclass
        """
        pass 