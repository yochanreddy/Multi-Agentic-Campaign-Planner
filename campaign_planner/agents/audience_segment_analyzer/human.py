from typing import Any, Dict
from campaign_planner.agents.base import BaseHumanNode
from langchain_core.runnables.config import RunnableConfig
from campaign_planner.utils import get_module_logger
from .output import OutputSchema
from langgraph.types import interrupt

logger = get_module_logger()


class HumanNode(BaseHumanNode):
    def get_human_validation(self, state: Dict[str, Any], config: RunnableConfig):
        """Get human validation and parse output state."""
        logger.debug(f"{config['configurable']['thread_id']} start")
        
        # Extract only the fields that match OutputSchema
        output_fields = {
            "age_group": state.get("age_group"),
            "gender": state.get("gender"),
            "interests": state.get("interests", []),
            "locations": state.get("locations", []),
            "psychographic_traits": state.get("psychographic_traits", []),
            "recommended_ad_platforms": state.get("recommended_ad_platforms", [])
        }
        
        # Validate the extracted fields
        output_data = OutputSchema.model_validate(output_fields)
        
        if config["configurable"].get("enable_user_validation", False):
            output_data = OutputSchema.model_validate(
                interrupt(OutputSchema.model_validate(output_fields))
            )
            
        logger.debug(f"{config['configurable']['thread_id']} finish")
        return output_data.model_dump()
