from pydantic import BaseModel, Field
from typing import Any, Dict

from campaign_planner.agents.base import BaseOutputNode
from langchain_core.runnables.config import RunnableConfig
from campaign_planner.utils import get_module_logger
from langchain.output_parsers import PydanticOutputParser

logger = get_module_logger()


class OutputSchema(BaseModel):
    industry: str = Field(..., description="Classified Industry Type")

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
