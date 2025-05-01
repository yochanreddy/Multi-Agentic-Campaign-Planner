from pydantic import BaseModel, Field
from typing import Any, Dict, Literal
import httpx
import json
import os
from dotenv import load_dotenv

from campaign_planner.agents.base import BaseOutputNode
from langchain_core.runnables.config import RunnableConfig
from campaign_planner.utils import get_module_logger
from langchain.output_parsers import PydanticOutputParser

logger = get_module_logger()
ChannelType = Literal["Meta", "Google", "LinkedIn", "TikTok"]

# Load environment variables
load_dotenv()

# Get API URL from environment variables
BUDGET_ALLOCATION_API_URL = os.getenv("BUDGET_ALLOCATION_API_URL", "https://nyx-ai-api.dev.nyx.today/nyx-ad-recommendation/v2/allocatebudget/")


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

    async def format_output(
        self, state: Dict[str, Any], config: RunnableConfig
    ) -> OutputSchema:
        """Format the output state"""
        logger.debug(f"{config['configurable']['thread_id']} start")
        
        # Log state value if it exists
        if "total_budget" in state:
            logger.info(f"State has total_budget: {state['total_budget']}")
        else:
            logger.info("State does not have total_budget")

        # Log message content
        last_message = state["messages"][-1]
        

        # Always parse the message to get channel_budget_allocation
        parsed_data: OutputSchema = self.output_parser.invoke(last_message)
        logger.info(f"Parsed channel_budget_allocation: {parsed_data.channel_budget_allocation}")

        # If total_budget exists in state, use it, otherwise use parsed value
        if "total_budget" in state:
            output_data = OutputSchema(
                total_budget=state["total_budget"],
                channel_budget_allocation=parsed_data.channel_budget_allocation
            )
            logger.info(f"Using state value for total_budget: {output_data.total_budget}")
        else:
            output_data = parsed_data
            logger.info(f"Using parsed message value for total_budget: {output_data.total_budget}")
            
        logger.debug(f"{config['configurable']['thread_id']} finish")
        
        # Make API call to budget allocation service
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info("Making API call to budget allocation service...")
                # Ensure channels is a list
                channels = state.get("recommended_ad_platforms", [])
                if isinstance(channels, str):
                    channels = [channels]
                elif not isinstance(channels, list):
                    channels = []
                
                # Process age range
                age_str = state.get("age_group", "")
                age_ranges = [age.strip() for age in age_str.split(",")]
                min_age = 18  # default minimum
                max_age = 100  # default maximum
                
                for age_range in age_ranges:
                    if age_range == "All":
                        continue
                    if "+" in age_range:
                        age = int(age_range.replace("+", ""))
                        max_age = max(max_age, age)
                    elif "-" in age_range:
                        start, end = map(int, age_range.split("-"))
                        min_age = min(min_age, start)
                        max_age = max(max_age, end)
                
                age_range = f"{min_age}-{max_age}"
                
                # Format start date to YYYY-MM-DD
                start_date = state.get("campaign_start_date", "")
                if start_date:
                    try:
                        # Parse the date in DD-MM-YYYY format
                        day, month, year = start_date.split("-")
                        # Reformat to YYYY-MM-DD
                        start_date = f"{year}-{month}-{day}"
                    except (ValueError, AttributeError):
                        logger.warning(f"Invalid date format: {start_date}, using default")
                        start_date = "2025-05-15"  # default date
                else:
                    start_date = "2025-05-15"  # default date
                
                request_payload = {
                    "campaign_objective": state.get("campaign_objective"),
                    "channels": channels,
                    "age": age_range,
                    "gender": state.get("gender", "All").capitalize(),
                    "location": state.get("locations")[0],
                    "start_date": start_date,
                    "cost": output_data.total_budget
                }
                
                # Convert to JSON string to ensure proper formatting
                json_payload = json.dumps(request_payload)
                logger.info(f"Request payload: {json_payload}")
                
                response = await client.post(
                    BUDGET_ALLOCATION_API_URL,
                    content=json_payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                api_response = response.json()
                logger.info(f"Budget allocation API call successful: {response.status_code}")
                logger.debug(f"Budget allocation API response: {api_response}")
                
                # Update channel_budget_allocation with API response
                if "allocations" in api_response:
                    output_data.channel_budget_allocation = api_response["allocations"]
                    logger.info(f"Updated channel_budget_allocation from API: {output_data.channel_budget_allocation}")
                
        except httpx.ConnectError as e:
            logger.error(f"Connection error: Could not connect to budget allocation service. Error: {str(e)}")
        except httpx.TimeoutException as e:
            logger.error(f"Timeout error: Budget allocation service request timed out. Error: {str(e)}")
        except httpx.HTTPStatusError as e:
            error_message = "Unknown error"
            try:
                error_response = e.response.json()
                error_message = error_response.get("detail", str(error_response))
            except:
                error_message = str(e)
            logger.error(f"HTTP error: Budget allocation service returned {e.response.status_code}. Error: {error_message}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: Could not parse budget allocation service response. Error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in budget allocation service call: {str(e)}")
            logger.exception("Full traceback:")
        
        return output_data.model_dump()
