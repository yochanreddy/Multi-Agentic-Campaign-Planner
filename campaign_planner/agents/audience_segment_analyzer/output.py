from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal
import httpx
import json
import ast
import struct
from itertools import chain, repeat
import urllib
import pandas as pd
from azure.identity import ClientSecretCredential
import pyodbc
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

from campaign_planner.agents.base import BaseOutputNode
from langchain_core.runnables.config import RunnableConfig
from campaign_planner.utils import get_module_logger
from langchain.output_parsers import PydanticOutputParser

logger = get_module_logger()

# Load environment variables for secure credential management
load_dotenv()

# Get API URLs from environment variables
OPTIMIZATION_API_URL = os.getenv("OPTIMIZATION_API_URL", "https://nyx-ai-api.dev.nyx.today/nyx-ad-recommendation/optimize")

# Fabric connection details
TENANT_ID = os.getenv("FABRIC_TENANT_ID")
CLIENT_ID = os.getenv("FABRIC_CLIENT_ID")
CLIENT_SECRET = os.getenv("FABRIC_CLIENT_SECRET")
RESOURCE_URL = os.getenv("FABRIC_RESOURCE_URL", "https://database.windows.net/.default")
SQL_ENDPOINT = os.getenv("FABRIC_SQL_ENDPOINT")
DATABASE = os.getenv("FABRIC_DATABASE")

def get_fabric_connection():
    """Create and return a Fabric connection"""
    try:
        # Validate required environment variables
        required_vars = {
            "FABRIC_TENANT_ID": TENANT_ID,
            "FABRIC_CLIENT_ID": CLIENT_ID,
            "FABRIC_CLIENT_SECRET": CLIENT_SECRET,
            "FABRIC_SQL_ENDPOINT": SQL_ENDPOINT,
            "FABRIC_DATABASE": DATABASE
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        # Create credential using service principal
        credential = ClientSecretCredential(
            tenant_id=TENANT_ID,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET
        )
        token_object = credential.get_token(RESOURCE_URL)

        # Create connection string
        connection_string = (
            f"Driver={{ODBC Driver 18 for SQL Server}};"
            f"Server={SQL_ENDPOINT},1433;"
            f"Database={DATABASE};"
            f"Encrypt=Yes;"
            f"TrustServerCertificate=No"
        )
        params = urllib.parse.quote(connection_string)

        # Prepare access token for ODBC
        token_as_bytes = bytes(token_object.token, "UTF-8")
        encoded_bytes = bytes(chain.from_iterable(zip(token_as_bytes, repeat(0))))
        token_bytes = struct.pack("<i", len(encoded_bytes)) + encoded_bytes
        attrs_before = {1256: token_bytes}  # SQL_COPT_SS_ACCESS_TOKEN

        # Create connection with token
        conn = pyodbc.connect(
            connection_string,
            attrs_before={1256: token_bytes}  # SQL_COPT_SS_ACCESS_TOKEN
        )
        
        # Create SQLAlchemy engine
        engine = create_engine(
            "mssql+pyodbc:///?odbc_connect={0}".format(params),
            connect_args={'attrs_before': attrs_before}
        )
        
        logger.info("Successfully initialized Fabric connection")
        return engine
    except Exception as e:
        logger.error(f"Failed to initialize Fabric connection: {str(e)}")
        raise

def map_campaign_objective(objective: str) -> str:
    """Map campaign objectives from enum values to standardized categories"""
    # Direct mapping from enum values to standardized categories
    mapping = {
        "Brand Awareness": "Awareness",
        "Traffic": "Traffic",
        "Engagement": "Engagement",
        "Lead Generation": "Lead Generation",
        "Shopping": "Sales/Revenue",
        "Website Conversion": "Conversions",
        "Video Views": "Video Views",
        "App Engagement": "Engagement",
        "App Install": "App Installs"
    }
    
    # Return mapped value if it exists, otherwise return "Other"
    return mapping.get(objective, "Other")

def get_goals_from_fabric(account_ids: List[str], campaign_objective: str) -> Dict[str, float]:
    """Get goals from Fabric in cascading manner"""
    # Map the campaign objective to standardized category
    mapped_objective = map_campaign_objective(campaign_objective)
    queries = []
    
    # Add first query if we have both account_ids and campaign_objective
    if account_ids and mapped_objective:
        queries.append({
            "query": f"""
            SELECT MAX(video_views) as views,
                   MAX(cost) as spend,
                   MAX(impressions) as impressions,
                   MAX(clicks) as clicks,
                   MAX(conversions) as conversions
            FROM [Gold_WH].[reporting].[merged_ads_final]
            WHERE account_id IN ({','.join([f"'{id}'" for id in account_ids])})
            AND campaign_objective = '{mapped_objective}'
            """,
            "description": "Query with account_ids and campaign_objective"
        })
    
    # Add second query if we have campaign_objective
    if mapped_objective:
        queries.append({
            "query": f"""
            SELECT MAX(video_views) as views,
                   MAX(cost) as spend,
                   MAX(impressions) as impressions,
                   MAX(clicks) as clicks,
                   MAX(conversions) as conversions
            FROM [Gold_WH].[reporting].[merged_ads_final]
            WHERE campaign_objective = '{mapped_objective}'
            """,
            "description": "Query with campaign_objective only"
        })
    
    # Always add the default query
    queries.append({
        "query": """
        SELECT MAX(video_views) as views,
               MAX(cost) as spend,
               MAX(impressions) as impressions,
               MAX(clicks) as clicks,
               MAX(conversions) as conversions
        FROM [Gold_WH].[reporting].[merged_ads_final]
        """,
        "description": "Default query without filters"
    })
    
    engine = get_fabric_connection()
    
    for query_info in queries:
        try:
            logger.info(f"Executing {query_info['description']}")
            df = pd.read_sql(query_info["query"], engine)
            
            # Check if all values are null
            if df.empty or df.iloc[0].isnull().all():
                logger.info(f"All values are null in {query_info['description']}, trying next query")
                continue
                
            goals = {}
            row = df.iloc[0]
            if pd.notnull(row.views): goals["views"] = float(row.views)
            if pd.notnull(row.spend): goals["spend"] = float(row.spend)
            if pd.notnull(row.impressions): goals["impressions"] = float(row.impressions)
            if pd.notnull(row.clicks): goals["clicks"] = float(row.clicks)
            if pd.notnull(row.conversions): goals["conversions"] = float(row.conversions)
            
            if goals:
                logger.info(f"Successfully retrieved goals using {query_info['description']}")
                logger.info(f"Retrieved goals from Fabric: {goals}")
                return goals
            else:
                logger.info(f"No non-null values found in {query_info['description']}, trying next query")
        except Exception as e:
            logger.error(f"Error executing Fabric query ({query_info['description']}): {str(e)}")
            continue
    
    logger.warning("No valid goals found in Fabric, skipping goals")
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
    recommended_ad_platforms_by_model: List[str] = Field(
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
        
        # Get goals from Fabric
        account_ids = state.get("account_ids")
        campaign_objective = state.get("campaign_objective")
        goals = get_goals_from_fabric(account_ids, campaign_objective)
        
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

                    # Update platforms from API response
                    if "platforms" in api_response:
                        output_data.recommended_ad_platforms_by_model = api_response["platforms"]
                        logger.info(f"Updated recommended_ad_platforms_by_model to: {output_data.recommended_ad_platforms_by_model}")

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
                    # Remove recommended_ad_platforms_by_model from output data on API failure
                    output_dict = output_data.model_dump()
                    output_dict.pop('recommended_ad_platforms_by_model', None)
                    logger.info("Removed recommended_ad_platforms_by_model from output data due to API failure")
                    return output_dict
                
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
