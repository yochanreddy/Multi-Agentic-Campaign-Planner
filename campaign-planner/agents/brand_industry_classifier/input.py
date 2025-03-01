from typing import Any, Dict

from agents.base import InputNode
from langchain_core.runnables.config import RunnableConfig
from utils import get_module_logger
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
        extra = "allow"


class Input(InputNode):
    def validate_and_parse(
        self, state: Dict[str, Any], config: RunnableConfig
    ) -> Dict[str, Any]:
        """Validate and parse input state"""
        logger.debug(f"{self.__class__.__name__} start")
        input_data = InputSchema.model_validate(state)
        logger.debug(f"{self.__class__.__name__} finish")
        return {"input": input_data}
