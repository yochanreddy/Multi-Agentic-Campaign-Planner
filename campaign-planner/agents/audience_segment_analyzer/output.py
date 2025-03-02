from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal

from agents.base import BaseOutputNode
from langchain_core.runnables.config import RunnableConfig
from utils import get_module_logger
from langchain.output_parsers import PydanticOutputParser

logger = get_module_logger()


class OutputSchema(BaseModel):
    age_group: str = Field(
        ...,
        description="Specific age range of target audience in 'min-max' format (e.g., '18-35', '25-44'). Must be realistic demographic segments.",
    )
    gender: Literal["male", "female", "others", "all"] = Field(
        ...,
        description="Target audience gender identity. Use 'all' for gender-neutral campaigns or when targeting multiple genders.",
    )
    interests: List[str] = Field(
        ...,
        description="Key topics, activities, hobbies and subject areas that the target audience actively engages with or shows affinity towards.",
    )
    locations: List[str] = Field(
        ...,
        description="Geographic targeting areas including cities, regions, or countries where the target audience is concentrated or likely to be found.",
    )
    psychographic_traits: List[str] = Field(
        ...,
        description="Personality characteristics, values, attitudes, aspirations, and lifestyle choices that define the target audience's decision-making and behavior patterns.",
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
