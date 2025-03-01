from pydantic import BaseModel, Field
from typing import Any, Dict

from agents.base import OutputNode
from langchain_core.runnables.config import RunnableConfig
from utils import get_module_logger
from langchain.output_parsers import PydanticOutputParser

logger = get_module_logger()


class OutputSchema(BaseModel):
    campaign_name: str = Field(
        ...,
        description="A unique campaign identifier combining brand, timing, audience, and theme elements separated by underscores (e.g., 'BrandName_Season_TargetAudience_Theme'). This name helps in easily identifying and distinguishing marketing campaigns across the platform.",
        examples=[
            "Nike_Summer2024_GenZ_Streetwear",
            "Apple_Q42023_Professionals_Innovation",
        ],
        min_length=5,
        max_length=100,
        pattern="^[A-Za-z0-9]+(?:_[A-Za-z0-9]+)*$",  # Ensures proper underscore separation
    )

    class Config:
        extra = "allow"


class Output(OutputNode):
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
