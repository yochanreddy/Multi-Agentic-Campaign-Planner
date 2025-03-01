from pydantic import BaseModel, Field
from typing import Any, Dict

from agents.base import OutputNode
from langchain_core.runnables.config import RunnableConfig
from utils import get_module_logger

logger = get_module_logger()


class OutputSchema(BaseModel):
    industry: str = Field(..., description="Classified Industry Type")

    class Config:
        extra = "allow"


class Output(OutputNode):
    def format_output(
        self, state: Dict[str, Any], config: RunnableConfig
    ) -> OutputSchema:
        """Format the output state"""
        logger.debug(f"{self.__class__.__name__} start")
        output_data = OutputSchema.model_validate(state)
        logger.debug(f"{self.__class__.__name__} finish")
        return {"industry": output_data["industry"]}
