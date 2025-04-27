from campaign_planner.agents.base import BaseRouterNode
from campaign_planner.utils import get_module_logger
from langchain_core.runnables.config import RunnableConfig
from campaign_planner.state import State

logger = get_module_logger()


class RouterNode(BaseRouterNode):
    def determine_next_step(self, state: State, config: RunnableConfig) -> str:
        logger.debug(f"{config['configurable']['thread_id']} start")
        intent = "finish"
        last_message = state.get("messages")[-1]
        if last_message.tool_calls:
            intent = "tool"
        logger.debug(f"{config['configurable']['thread_id']} finish")
        return intent
