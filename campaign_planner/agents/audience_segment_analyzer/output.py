from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal
import httpx
import json
import ast
from google.cloud import bigquery
import os
from dotenv import load_dotenv
from google.oauth2 import service_account

from campaign_planner.agents.base import BaseOutputNode
from langchain_core.runnables.config import RunnableConfig
from campaign_planner.utils import get_module_logger
from langchain.output_parsers import PydanticOutputParser

logger = get_module_logger()

# Load environment variables for secure credential management
load_dotenv()

# Get API URLs from environment variables
OPTIMIZATION_API_URL = os.getenv("OPTIMIZATION_API_URL", "https://nyx-ai-api.dev.nyx.today/nyx-ad-recommendation/optimize")
BIGQUERY_TABLE = os.getenv("BIGQUERY_TABLE", "nyx-agents.reporting.recomm_engine_combined")

# BigQuery credentials configuration for authentication
credentials_dict = {
    "type": os.getenv("GCP_TYPE"),
    "project_id": os.getenv("GCP_PROJECT_ID"),
    "private_key_id": os.getenv("GCP_PRI_KEY_ID"),
    "private_key": os.getenv("GCP_PRI_KEY").replace('\\n', '\n'),
    "client_email": os.getenv("GCP_CLIENT_EMAIL"),
    "client_id": os.getenv("GCP_CLIENT_ID"),
    "auth_uri": os.getenv("GCP_AUTH_URI"),
    "token_uri": os.getenv("GCP_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("GCP_AUTH_PROVIDER"),
    "client_x509_cert_url": os.getenv("GCP_CLIENT_CERT_URL"),
    "universe_domain": os.getenv("GCP_UNIVERSE_DOMAIN")
}

# Initialize BigQuery client with credentials from environment
try:
    credentials = service_account.Credentials.from_service_account_info(credentials_dict)
    client = bigquery.Client(credentials=credentials, project=credentials_dict["project_id"])
    logger.info("Successfully initialized BigQuery client with credentials")
except Exception as e:
    logger.error(f"Failed to initialize BigQuery client: {str(e)}")
    logger.warning("Using default client without credentials")
    client = bigquery.Client()

def get_goals_from_bigquery(account_ids: List[str], campaign_objective: str) -> Dict[str, float]:
    """Get goals from BigQuery in cascading manner"""
    if not account_ids or not campaign_objective:
        logger.warning("Missing account_ids or campaign_objective, skipping BigQuery goals")
        return {}

    queries = [
        {
            "query": f"""
            SELECT max(views) as views,
                   max(spend) as spend,
                   max(impressions) as impressions,
                   max(clicks) as clicks,
                   max(conversions) as conversions
            FROM `{BIGQUERY_TABLE}`
            WHERE account_id in({','.join([f'"{id}"' for id in account_ids])})
            AND campaign_objective="{campaign_objective}"
            """,
            "description": "Query with account_ids and campaign_objective"
        },
        {
            "query": f"""
            SELECT max(views) as views,
                   max(spend) as spend,
                   max(impressions) as impressions,
                   max(clicks) as clicks,
                   max(conversions) as conversions
            FROM `{BIGQUERY_TABLE}`
            WHERE campaign_objective="{campaign_objective}"
            """,
            "description": "Query with campaign_objective only"
        },
        {
            "query": f"""
            SELECT max(views) as views,
                   max(spend) as spend,
                   max(impressions) as impressions,
                   max(clicks) as clicks,
                   max(conversions) as conversions
            FROM `{BIGQUERY_TABLE}`
            """,
            "description": "Default query without filters"
        }
    ]
    
    for query_info in queries:
        try:
            logger.info(f"Executing {query_info['description']}")
            query_job = client.query(query_info["query"])
            results = query_job.result()
            row = next(results, None)
            
            # Check if all values are null
            if row and all(value is None for value in [row.views, row.spend, row.impressions, row.clicks, row.conversions]):
                logger.info(f"All values are null in {query_info['description']}, trying next query")
                continue
                
            if row:
                goals = {}
                if row.views is not None: goals["views"] = float(row.views)
                if row.spend is not None: goals["spend"] = float(row.spend)
                if row.impressions is not None: goals["impressions"] = float(row.impressions)
                if row.clicks is not None: goals["clicks"] = float(row.clicks)
                if row.conversions is not None: goals["conversions"] = float(row.conversions)
                
                if goals:
                    logger.info(f"Successfully retrieved goals using {query_info['description']}")
                    logger.info(f"Retrieved goals from BigQuery: {goals}")
                    return goals
                else:
                    logger.info(f"No non-null values found in {query_info['description']}, trying next query")
        except Exception as e:
            logger.error(f"Error executing BigQuery query ({query_info['description']}): {str(e)}")
            continue
    
    logger.warning("No valid goals found in BigQuery, skipping goals")
    return {}

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

    total_budget: float = Field(
        ...,
        description="The total daily budget predicted to run a campaign based on the previous outputs",
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
       

        last_message = state["messages"][-1]
        output_data: OutputSchema = self.output_parser.invoke(last_message)
        
        # Log initial output data
        logger.info(f"Initial output data: {output_data.model_dump()}")
        
        # Get goals from BigQuery
        account_ids = state.get("account_ids")
        campaign_objective = state.get("campaign_objective")
        goals = get_goals_from_bigquery(account_ids, campaign_objective)
        
        # Make API call to nyx-ai-api
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                logger.info("Making API call to optimization service...")
                api_payload = {
                    "account_ids": account_ids
                }
                
                # Only add goals if we have any
                if goals:
                    api_payload["goals"] = {
                        "spend_goal": goals.get("spend", 0),
                        "impressions_goal": goals.get("impressions", 0),
                        "views_goal": goals.get("views", 0),
                        "clicks_goal": goals.get("clicks", 0),
                        "conversions_goal": goals.get("conversions", 0)
                    }
                
                response = await client.post(
                    OPTIMIZATION_API_URL,
                    json=api_payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
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

                    # Update total_budget from API response
                    if "budget" in api_response:
                        output_data.total_budget = float(api_response["budget"])
                        logger.info(f"Updated total_budget to: {output_data.total_budget}")
                else:
                    logger.warning(f"API call returned non-200 status code: {response.status_code}")
                    try:
                        error_response = response.json()
                        logger.warning(f"API error response: {error_response}")
                    except:
                        logger.warning(f"API error response: {response.text}")
                
        except httpx.ConnectError as e:
            logger.warning(f"Connection error: Could not connect to optimization service. Error: {str(e)}")
        except httpx.TimeoutException as e:
            logger.warning(f"Timeout error: Optimization service request timed out. Error: {str(e)}")
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error: Optimization service returned {e.response.status_code}. Error: {str(e)}")
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error: Could not parse optimization service response. Error: {str(e)}")
        except Exception as e:
            logger.warning(f"Unexpected error in optimization service call: {str(e)}")
            logger.exception("Full traceback:")
        
        logger.debug(f"{config['configurable']['thread_id']} finish")
        return output_data.model_dump()
