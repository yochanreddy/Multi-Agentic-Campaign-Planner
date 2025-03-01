from typing import Any, Dict, List, Literal

from agents.base import InputNode
from langchain_core.runnables.config import RunnableConfig
from utils import get_module_logger
from pydantic import BaseModel, Field

logger = get_module_logger()
ChannelType = Literal["Meta", "Google", "LinkedIn", "TikTok"]


class InputSchema(BaseModel):
    brand_name: str = Field(..., description="Name of Brand")
    brand_description: str = Field(..., description="Description of Brand")
    campaign_objective: str = Field(..., description="Objective of the campaign")
    industry: str = Field(..., description="type of industry")
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
    integrated_ad_platforms: List[ChannelType] = Field(
        ...,
        description="Digital advertising platforms integrated with the platform where campaigns could run",
    )

    class Config:
        extra = "allow"


class Input(InputNode):
    def validate_and_parse(
        self, state: Dict[str, Any], config: RunnableConfig
    ) -> Dict[str, Any]:
        """Validate and parse input state"""
        logger.debug(f"{config['configurable']['thread_id']} start")
        input_data = InputSchema.model_validate(state)
        logger.debug(f"{config['configurable']['thread_id']} finish")
        return {"input": input_data}
