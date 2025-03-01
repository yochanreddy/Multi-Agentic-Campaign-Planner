from agents.base import RouterNode
from utils import get_module_logger
from langchain_core.runnables.config import RunnableConfig
from state import State

logger = get_module_logger()


class Router(RouterNode):
    def determine_next_step(self, state: State, config: RunnableConfig) -> str:
        logger.debug(f"{config['configurable']['thread_id']} start")
        intent = "finish"
        last_message = state.get("messages")[-1]
        if last_message.tool_calls:
            intent = "tool"
        logger.debug(f"{config['configurable']['thread_id']} finish")
        return intent
