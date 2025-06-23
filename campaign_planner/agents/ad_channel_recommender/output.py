from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal

from campaign_planner.agents.base import BaseOutputNode
from langchain_core.runnables.config import RunnableConfig
from campaign_planner.utils import get_module_logger
from langchain.output_parsers import PydanticOutputParser

logger = get_module_logger()
ChannelType = Literal["Meta", "Google", "LinkedIn"]


class OutputSchema(BaseModel):
    recommended_ad_platforms: List[ChannelType] = Field(
        ...,
        description="Recommended Digital advertising platforms integrated with the platform where campaigns will run",
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

        # Log state value if it exists
        if "recommended_ad_platforms_by_model" in state:
            logger.info(f"State has recommended_ad_platforms_by_model: {state['recommended_ad_platforms_by_model']}")
        else:
            logger.info("State does not have recommended_ad_platforms_by_model")

        # Log message content
        last_message = state["messages"][-1]
        

        # If recommended_ad_platforms already exists in state, use it
        if "recommended_ad_platforms_by_model" in state and state["recommended_ad_platforms_by_model"]:
            output_data = OutputSchema(recommended_ad_platforms=state["recommended_ad_platforms_by_model"])
            logger.info(f"Using state value: {output_data.recommended_ad_platforms}")
        else:
            # Otherwise, parse from the message
            output_data: OutputSchema = self.output_parser.invoke(last_message)
            logger.info(f"Using parsed message value: {output_data.recommended_ad_platforms}")
            
        logger.debug(f"{config['configurable']['thread_id']} finish")
        return output_data.model_dump()
