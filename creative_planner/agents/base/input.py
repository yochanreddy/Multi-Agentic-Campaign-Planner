from abc import ABC, abstractmethod
from typing import Any
from langchain_core.runnables.config import RunnableConfig
from creative_planner.utils import get_module_logger

logger = get_module_logger()


class BaseInputNode(ABC):
    @abstractmethod
    def validate_and_parse(self, state: Any, config: RunnableConfig) -> Any:
        """
        Validate and parse input state.

        Args:
            state (Any): Raw input state to be validated and parsed

        Returns:
            Any: Validated and parsed state ready for processing

        Raises:
            NotImplementedError: Must be implemented in a subclass
        """
        pass 