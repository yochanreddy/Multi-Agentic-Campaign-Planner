from abc import ABC, abstractmethod
from typing import Any, Dict
from langchain_core.runnables.config import RunnableConfig
from creative_planner.utils import get_module_logger

logger = get_module_logger()


class BaseStateNode(ABC):
    @abstractmethod
    def update_state(self, state: Any, config: RunnableConfig) -> Dict[str, Any]:
        """
        Updates the state based on the current state and configuration.

        Args:
            state (Any): Current state to be updated
            config (RunnableConfig): Configuration parameters for the state update

        Returns:
            Dict[str, Any]: Updated state dictionary

        Raises:
            NotImplementedError: Must be implemented in a subclass
        """
        pass 