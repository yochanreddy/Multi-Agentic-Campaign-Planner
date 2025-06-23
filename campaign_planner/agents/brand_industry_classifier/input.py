from typing import Any, Dict

from campaign_planner.agents.base import BaseInputNode
from langchain_core.runnables.config import RunnableConfig
from campaign_planner.utils import get_module_logger
from typing import Optional
from pydantic import BaseModel, Field

logger = get_module_logger()


class InputSchema(BaseModel):
    brand_name: str = Field(..., description="Name of Brand")
    brand_description: str = Field(..., description="Description of Brand")
    product_name: Optional[str] = Field(default="", description="Product of Brand")
    product_description: Optional[str] = Field(
        default="", description="Description of Product"
    )
    website: Optional[str] = Field(default="", description="Website of Brand")

    class Config:
        extra = "ignore"


class InputNode(BaseInputNode):
    def validate_and_parse(
        self, state: Dict[str, Any], config: RunnableConfig
    ) -> Dict[str, Any]:
        """Validate and parse input state"""
        logger.debug(f"{config['configurable']['thread_id']} start")
        input_data = InputSchema.model_validate(state)
        logger.debug(f"{config['configurable']['thread_id']} finish")
        return input_data.model_dump()
