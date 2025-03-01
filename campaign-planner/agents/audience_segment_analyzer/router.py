from agents.base import RouterNode
from utils import get_module_logger
from langchain_core.runnables.config import RunnableConfig
from .state import LocalState

logger = get_module_logger()


class Router(RouterNode):
    def determine_next_step(self, state: LocalState, config: RunnableConfig) -> str:
        logger.debug(f"{self.__class__.__name__} start")
        intent = "finish"
        last_message = state.get("messages")[-1]
        if last_message.tool_calls:
            intent = "tool"
        logger.debug(f"{self.__class__.__name__} finish")
        return intent
