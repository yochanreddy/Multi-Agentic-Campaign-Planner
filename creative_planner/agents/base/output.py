from abc import ABC, abstractmethod
from typing import Any
from langchain_core.runnables.config import RunnableConfig
from creative_planner.utils import get_module_logger

logger = get_module_logger()


class BaseOutputNode(ABC):
    @abstractmethod
    def format_output(self, state: Any, config: RunnableConfig) -> Any:
        """
        Format the output state for final presentation or storage.

        Args:
            state (Any): Processed state to be formatted

        Returns:
            Any: Formatted output ready for presentation or further processing

        Raises:
            NotImplementedError: Must be implemented in a subclass
        """
        pass 