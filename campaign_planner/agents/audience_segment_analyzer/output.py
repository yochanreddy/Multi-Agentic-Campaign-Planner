from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal
import httpx
import json
import ast

from campaign_planner.agents.base import BaseOutputNode
from langchain_core.runnables.config import RunnableConfig
from campaign_planner.utils import get_module_logger
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
    recommended_ad_platforms: List[str] = Field(
        ...,
        description="Recommended Digital advertising platforms integrated with the platform where campaigns will run",
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
        logger.info(f"Initial state: {state}")

        last_message = state["messages"][-1]
        output_data: OutputSchema = self.output_parser.invoke(last_message)
        
        # Log initial output data
        logger.info(f"Initial output data: {output_data.model_dump()}")
        
        # Make API call to nyx-ai-api
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info("Making API call to optimization service...")
                response = await client.post(
                    "http://0.0.0.0:5004/optimize",
                    json={
                        "goals": {
                            "spend_goal": 2000,
                            "impressions_goal": 80000,
                            "views_goal": 40000,
                            "clicks_goal": 2000,
                            "conversions_goal": 80
                        },
                        "account_ids": [
                            "6694298580",
                            "350653016327812"
                        ]
                    },
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                api_response = response.json()
                logger.info(f"API call successful: {response.status_code}")
                logger.debug(f"API response: {api_response}")
                
                # Update age_group from API response
                if "age_range" in api_response:
                    # Parse the string representation of list into actual list
                    age_ranges = ast.literal_eval(api_response["age_range"])
                    if age_ranges:
                        # Combine all age ranges into a comma-separated string
                        output_data.age_group = ", ".join(age_ranges)
                        logger.info(f"Updated age_group to: {output_data.age_group}")

                # Update gender from API response
                if "gender" in api_response:
                    # Convert gender to lowercase to match the Literal type
                    output_data.gender = api_response["gender"].lower()
                    logger.info(f"Updated gender to: {output_data.gender}")

                # Update recommended_ad_platforms from API response
                if "platforms" in api_response:
                    # Update platforms list
                    output_data.recommended_ad_platforms = api_response["platforms"]
                    logger.info(f"Updated recommended_ad_platforms to: {output_data.recommended_ad_platforms}")
                    
                # Update locations from API response
                if "countries" in api_response:
                    # Parse the string representation of list into actual list
                    countries = api_response["countries"]
                    if isinstance(countries, str):
                        # Remove any extra quotes and parse the list
                        countries = countries.strip('"\'')  # Remove outer quotes
                        countries = ast.literal_eval(countries)
                    output_data.locations = countries
                    logger.info(f"Updated locations to: {output_data.locations}")

        except httpx.ConnectError as e:
            logger.error(f"Connection error: Could not connect to optimization service. Error: {str(e)}")
        except httpx.TimeoutException as e:
            logger.error(f"Timeout error: Optimization service request timed out. Error: {str(e)}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: Optimization service returned {e.response.status_code}. Error: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: Could not parse optimization service response. Error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in optimization service call: {str(e)}")
            logger.exception("Full traceback:")
        
        logger.debug(f"{config['configurable']['thread_id']} finish")
        return output_data.model_dump()
