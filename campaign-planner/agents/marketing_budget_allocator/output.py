from pydantic import BaseModel, Field
from typing import Any, Dict, Literal

from agents.base import BaseOutputNode
from langchain_core.runnables.config import RunnableConfig
from utils import get_module_logger
from langchain.output_parsers import PydanticOutputParser

logger = get_module_logger()
ChannelType = Literal["Meta", "Google", "LinkedIn", "TikTok"]


class OutputSchema(BaseModel):
    total_budget: float = Field(
        description="The total daily budget predicted to run a campaign based on the previous outputs"
    )
    channel_budget_allocation: Dict[ChannelType, float] = Field(
        description="A dictionary with the recommended channel names as keys and their respective daily budget allocations in INR"
    )

    class Config:
        extra = "ignore"


class OutputNode(BaseOutputNode):
    output_parser = PydanticOutputParser(pydantic_object=OutputSchema)

    def __init__(self):
        super().__init__()

    def format_output(
        self, state: Dict[str, Any], config: RunnableConfig
    ) -> OutputSchema:
        """Format the output state"""
        logger.debug(f"{config['configurable']['thread_id']} start")

        last_message = state["messages"][-1]
        output_data: OutputSchema = self.output_parser.invoke(last_message)
        logger.debug(f"{config['configurable']['thread_id']} finish")
        return output_data.model_dump()
