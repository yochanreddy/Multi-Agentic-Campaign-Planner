import os
import logging
from typing import List, Literal, Optional, Dict
import uuid
from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.memory import MemorySaver
from psycopg_pool import AsyncConnectionPool
from pydantic import BaseModel, Field
from campaign_planner.utils import load_config, draw_mermaid_graph
from creative_planner.graph import CreativePlanner
from contextlib import asynccontextmanager
from campaign_planner.graph import CampaignPlanner
from enum import Enum
from fastapi import HTTPException
from creative_planner.utils.logging_config import configure_logging
from creative_planner.utils.storage import get_signed_url, save_image
from dotenv import load_dotenv
from campaign_objective_planner.graph import CampaignObjectiveGraph


workflow = None
creative_workflow = None
objective_workflow = None

class ChannelType(str, Enum):
    META = "Meta"
    GOOGLE = "Google"
    LINKEDIN = "LinkedIn"
    TIKTOK = "TikTok"

config = None

# Configure logging
configure_logging()
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get root path from environment variable
ROOT_PATH = os.getenv("ROOT_PATH", "/nyx-campaign-agent")

class ProcessingStatus(str, Enum):
    QUEUED = "QUEUED"
    BUILDING = "BUILDING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global workflow
    global creative_workflow
    global objective_workflow
    global config

    config = load_config()
    config["LOG_LEVEL"] = os.getenv("LOG_LEVEL", "INFO")
    
    if config["LOG_LEVEL"].lower() == "debug":
        config["checkpointer"] = MemorySaver()
        workflow = CampaignPlanner(config).get_compiled_graph()
        creative_workflow = CreativePlanner(config).get_compiled_graph()
        objective_workflow = CampaignObjectiveGraph(config).get_compiled_graph()
        # draw_mermaid_graph(workflow)
        # draw_mermaid_graph(creative_workflow)
        yield
    else:
        async with AsyncConnectionPool(
            "postgresql://{username}:{password}@{host}:5432/{database_name}".format(
                host=os.getenv("PGSQL_HOST"),
                database_name=os.getenv("PGSQL_DATABASE_NAME"),
                username=os.getenv("PGSQL_USERNAME"),
                password=os.getenv("PGSQL_PASSWORD"),
            ),
            kwargs={"autocommit": True},
            max_size=20,
        ) as pool:
            checkpointer = AsyncPostgresSaver(pool)
            await checkpointer.setup()
            config["checkpointer"] = checkpointer

            workflow = CampaignPlanner(config).get_compiled_graph()
            creative_workflow = CreativePlanner(config).get_compiled_graph()
            objective_workflow = CampaignObjectiveGraph(config).get_compiled_graph()
            yield

    logger.info("Workflow initialized successfully")


class CampaignSubmitRequest(BaseModel):
    brand_description: str = Field(
        description="Comprehensive description of the brand's identity, values and market positioning"
    )
    brand_name: str = Field(
        description="Official registered name of the brand or company"
    )
    product_description: str = Field(
        description="Detailed explanation of product features, benefits and unique selling points"
    )
    product_name: str = Field(
        description="Specific name or model of the product being advertised"
    )
    website: str = Field(
        description="Full URL of the brand's or product's landing page"
    )
    campaign_objective: str = Field(
        description="Primary marketing goal (e.g. 'Brand Awareness', 'Lead Generation', 'Sales Conversion')"
    )
    integrated_ad_platforms: List[ChannelType] = Field(
        description="Digital advertising platforms where campaigns will run (e.g. 'Meta', 'Google', 'LinkedIn', 'TikTok')"
    )
    account_ids: List[str] = Field(
        description="List of account IDs associated with the campaign",
        default_factory=list
    )

    class Config:
        json_schema_extra = {
            "example": {
                "brand_name": "Zepto",
                "website": "www.zeptonow.com",
                "brand_description": "Top 3 quick delivery service startup",
                "product_name": "Zepto Cafe",
                "product_description": "Zepto Cafe is a 10-minute food delivery service offering a diverse menu of freshly prepared snacks, beverages, and meals, combining speed and quality to cater to fast-paced urban lifestyles.",
                "campaign_objective": "Increase Brand Awareness",
                "integrated_ad_platforms": ["Meta", "Google"],
                "account_ids": [ "6694298580", "350653016327812"]
            }
        }


class CreativeSubmitRequest(BaseModel):
    brand_name: str = Field(default=None, description="Official registered name of the brand or company")
    brand_description: str = Field(default=None, description="Comprehensive description of the brand's identity, values and market positioning")
    product_name: Optional[str] = Field(default=None, description="Specific name or model of the product being advertised")
    product_description: Optional[str] = Field(default=None, description="Detailed explanation of product features, benefits and unique selling points")
    website: Optional[str] = Field(default=None, description="Full URL of the brand's or product's landing page")
    campaign_objective: str = Field(default=None, description="Primary marketing goal (e.g. 'Brand Awareness', 'Lead Generation', 'Sales Conversion')")
    integrated_ad_platforms: Optional[List] = Field(default=None, description="Digital advertising platforms where campaigns will run")
    industry: Optional[str] = Field(default=None, description="Business sector or market category (e.g. 'Retail', 'Technology', 'Healthcare')")
    age_group: str = Field(default=None, description="Target demographic age range (e.g. '18-24', '25-34', '35-44')")
    gender: str = Field(default=None, description="Target audience gender identity ('Male', 'Female', 'All')")
    interests: List[str] = Field(default=None, description="Specific hobbies, activities and topics that appeal to the target audience")
    locations: List[str] = Field(default=None, description="Geographic targeting areas including cities, regions or countries")
    campaign_name: str = Field(default=None, description="A unique campaign identifier combining brand, timing, audience, and theme elements")
    psychographic_traits:List[str] = Field(default=None, description="Psychological and behavioral characteristics of target audience")
    recommended_ad_platforms: Optional[List] = Field(default=None, description="Recommended Digital advertising platforms integrated with the platform")
    campaign_start_date: Optional[str] = Field(default=None, description="Starting date of the marketing campaign (format: YYYY-MM-DD)")
    campaign_end_date: Optional[str] = Field(default=None, description="Ending date of the marketing campaign (format: YYYY-MM-DD)")
    total_budget: Optional[float] = Field(default=None, description="The total daily budget predicted to run a campaign based on the previous outputs")
    channel_budget_allocation: Optional[Dict[str, float]] = Field(default=None, description="A dictionary with the recommended channel names as keys and their respective daily budget allocations")
    user_prompt: Optional[str] = Field(default=None, description="Optional user-provided creative direction or specific requirements for the campaign")

    class Config:
        json_schema_extra = {
            "example": {
                "brand_name": "UrbanBite",
                "website": "www.urbanbite.com",
                "brand_description": "UrbanBite is a premium meal delivery service specializing in healthy, chef-crafted meals for urban professionals. We focus on locally-sourced ingredients, sustainable packaging, and quick delivery within 30 minutes.",
                "product_name": "UrbanBite Premium Subscription",
                "product_description": "Our Premium Subscription offers 10 chef-curated meals per week, with options for breakfast, lunch, and dinner. Each meal is nutritionally balanced, comes with detailed macros, and can be customized for dietary preferences.",
                "campaign_objective": "Lead Generation",
                "integrated_ad_platforms": ["Meta", "Google", "LinkedIn"],
                "industry": "Food Delivery",
                "age_group": "25-34",
                "gender": "All",
                "interests": ["Healthy Eating", "Fitness", "Sustainability"],
                "locations": ["New York", "San Francisco", "Los Angeles"],
                "psychographic_traits": ["Health-conscious", "Time-poor", "Quality-focused"],
                "campaign_name": "UrbanBite_Healthy_Living_2024",
                "recommended_ad_platforms": ["Meta", "Google", "LinkedIn"],
                "campaign_start_date": "2024-06-01",
                "campaign_end_date": "2024-08-31",
                "total_budget": 5000.0,
                "channel_budget_allocation": {
                    "Meta": 2000.0,
                    "Google": 2000.0,
                    "LinkedIn": 1000.0
                },
                "user_prompt": "Focus on highlighting the convenience and health benefits of our meal delivery service, with emphasis on the 30-minute delivery guarantee and locally-sourced ingredients."
            }
        }


class SubmitResponse(BaseModel):
    request_id: str = Field(description="unique request id")


class StatusResponse(BaseModel):
    processing_status: str = Field(description="current processing status")
    processing_node: str = Field(description="current processing node", default="")


class CampaignResultResponse(BaseModel):
    age_group: str = Field(
        description="Target demographic age range (e.g. '18-24', '25-34', '35-44')"
    )
    brand_description: str = Field(
        description="Comprehensive description of the brand's identity, values and market positioning"
    )
    brand_name: str = Field(
        description="Official registered name of the brand or company"
    )
    campaign_objective: str = Field(
        description="Primary marketing goal (e.g. 'Brand Awareness', 'Lead Generation', 'Sales Conversion')"
    )
    gender: str = Field(
        description="Target audience gender identity ('Male', 'Female', 'All')"
    )
    industry: str = Field(
        description="Business sector or market category (e.g. 'Retail', 'Technology', 'Healthcare')"
    )
    interests: List[str] = Field(
        description="Specific hobbies, activities and topics that appeal to the target audience"
    )
    locations: List[str] = Field(
        description="Geographic targeting areas including cities, regions or countries"
    )
    product_description: str = Field(
        description="Detailed explanation of product features, benefits and unique selling points"
    )
    product_name: str = Field(
        description="Specific name or model of the product being advertised"
    )
    psychographic_traits: List[str] = Field(
        description="Psychological and behavioral characteristics of target audience (e.g. 'Environmentally conscious', 'Tech-savvy', 'Health-oriented')"
    )
    website: str = Field(
        description="Full URL of the brand's or product's landing page"
    )
    integrated_ad_platforms: List[str] = Field(
        description="Digital advertising platforms where campaigns will run (e.g. 'Meta', 'Google', 'LinkedIn', 'TikTok')"
    )
    recommended_ad_platforms: List[str] = Field(
        description="Recommended Digital advertising platforms integrated with the platform where campaigns will run"
    )
    campaign_name: str = Field(
        description="A unique campaign identifier combining brand, timing, audience, and theme elements separated by underscores"
    )
    campaign_start_date: str = Field(
        description="Starting date of the marketing campaign (format: DD-MM-YYYY)"
    )
    campaign_end_date: str = Field(
        description="Ending date of the marketing campaign (format: DD-MM-YYYY)"
    )
    total_budget: float = Field(
        description="The total daily budget predicted to run a campaign based on the previous outputs"
    )
    channel_budget_allocation: dict = Field(
        description="A dictionary with the recommended channel names as keys and their respective daily budget allocations in INR",
    )

    class Config:
        extra = "ignore"


class CreativeResultResponse(BaseModel):
    """Response model for getting creative plan results"""
    signed_url: str = Field(..., description="Signed URL for the final creative image")


class CampaignObjectiveRequest(BaseModel):
    brand_name: Optional[str] = Field(
        default=None,
        description="Official registered name of the brand or company"
    )
    brand_description: Optional[str] = Field(
        default=None,
        description="Comprehensive description of the brand's identity, values and market positioning"
    )
    website_url: Optional[str] = Field(
        default=None,
        description="Full URL of the brand's website"
    )
    campaign_url: Optional[str] = Field(
        default=None,
        description="Full URL of the campaign landing page"
    )
    user_prompt: Optional[str] = Field(
        default=None,
        description="Optional user-provided description of the intended campaign objective or marketing goals"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "brand_name": "UrbanBite",
                "brand_description": "UrbanBite is a premium meal delivery service specializing in healthy, chef-crafted meals for urban professionals. We focus on locally-sourced ingredients, sustainable packaging, and quick delivery within 30 minutes.",
                "website_url": "www.urbanbite.com",
                "campaign_url": "www.urbanbite.com/summer-promo",
                "user_prompt": "We want to increase our customer base and get more people to try our service for the first time. We're also looking to promote our new loyalty program."
            }
        }


class CampaignObjectiveResponse(BaseModel):
    campaign_objective: str = Field(
        description="Selected campaign objective based on brand analysis"
    )
    reasoning: str = Field(
        description="Explanation of why this objective was selected"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "campaign_objective": "Brand Awareness",
                "reasoning": "Based on the brand description and website analysis, Brand Awareness was selected as the primary objective because UrbanBite is a new premium service entering the market and needs to establish its brand identity and value proposition."
            }
        }


app = FastAPI(
    lifespan=lifespan,
    title="Nyx Campaign Agent API",
    description="API for generating and managing marketing campaigns and creatives",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    root_path=ROOT_PATH
)

# Update CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
    expose_headers=["*"]  # Expose all headers
)

# Add a specific route for OpenAPI spec
@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_schema():
    return app.openapi()


@app.post("/request_campaign_plan", 
    response_model=SubmitResponse,
    summary="Submit a new campaign planning request",
    description="Initiates the process of generating a comprehensive marketing campaign plan based on provided brand and target audience information.",
    response_description="Returns a unique request ID to track the campaign planning progress"
)
async def request_campaign_plan(
    request: CampaignSubmitRequest, 
    background_tasks: BackgroundTasks
) -> SubmitResponse:
    response = SubmitResponse(request_id=str(uuid.uuid4()))

    thread_config = {
        "configurable": {
            "thread_id": response.request_id,
        }
    }

    background_tasks.add_task(
        workflow.ainvoke, request.model_dump(), config=thread_config
    )

    return response


@app.get("/status_campaign_plan/{request_id}", 
    response_model=StatusResponse,
    summary="Check campaign planning status",
    description="Retrieves the current status of a campaign planning request, including the processing node if still in progress.",
    response_description="Returns the current processing status and node information"
)
async def status_campaign_plan(request_id: str) -> StatusResponse:
    # Clean the thread ID by removing any newline characters
    request_id = request_id.strip()
    thread_config = {
        "configurable": {
            "thread_id": request_id,
        }
    }
    current_state = await workflow.aget_state(thread_config)


    if current_state.next:
        response = StatusResponse(
            processing_status=ProcessingStatus.BUILDING,
            processing_node=current_state.next[0],
        )
    else:
        response = StatusResponse(processing_status=ProcessingStatus.COMPLETE)

    return response


@app.get("/get_campaign_plan/{request_id}", 
    response_model=CampaignResultResponse,
    summary="Get completed campaign plan",
    description="Retrieves the final campaign plan results including target audience, budget allocation, and platform recommendations.",
    response_description="Returns the complete campaign plan details"
)
async def get_campaign_plan(request_id: str) -> CampaignResultResponse:
    thread_config = {
        "configurable": {
            "thread_id": request_id,
        }
    }
    current_state = await workflow.aget_state(thread_config)

    return CampaignResultResponse(
        age_group=current_state.values.get("age_group", ""),
        brand_description=current_state.values.get("brand_description", ""),
        brand_name=current_state.values.get("brand_name", ""),
        campaign_objective=current_state.values.get("campaign_objective", ""),
        gender=current_state.values.get("gender", ""),
        industry=current_state.values.get("industry", ""),
        interests=current_state.values.get("interests", []),
        locations=current_state.values.get("locations", []),
        product_description=current_state.values.get("product_description", ""),
        product_name=current_state.values.get("product_name", ""),
        psychographic_traits=current_state.values.get("psychographic_traits", []),
        website=current_state.values.get("website", ""),
        integrated_ad_platforms=current_state.values.get("integrated_ad_platforms", []),
        recommended_ad_platforms=current_state.values.get("recommended_ad_platforms", []),
        campaign_name=current_state.values.get("campaign_name", ""),
        campaign_start_date=current_state.values.get("campaign_start_date", ""),
        campaign_end_date=current_state.values.get("campaign_end_date", ""),
        total_budget=current_state.values.get("total_budget", 0.0),
        channel_budget_allocation=current_state.values.get("channel_budget_allocation", {})
    )


@app.post("/request_creative_plan", 
    response_model=SubmitResponse,
    summary="Submit a new creative planning request",
    description="Initiates the process of generating creative assets for a marketing campaign based on the provided campaign details.",
    response_description="Returns a unique request ID to track the creative planning progress"
)
async def request_creative_plan(
    request: CreativeSubmitRequest, 
    background_tasks: BackgroundTasks
) -> SubmitResponse:
    response = SubmitResponse(request_id=str(uuid.uuid4()))

    thread_config = {
        "configurable": {
            "thread_id": response.request_id,
        }
    }

    background_tasks.add_task(
        creative_workflow.ainvoke, request.model_dump(), config=thread_config
    )

    return response


@app.get("/status_creative_plan/{request_id}", 
    response_model=StatusResponse,
    summary="Check creative planning status",
    description="Retrieves the current status of a creative planning request, including the processing node if still in progress.",
    response_description="Returns the current processing status and node information"
)
async def status_creative_plan(request_id: str) -> StatusResponse:
    # Clean the thread ID by removing any newline characters
    request_id = request_id.strip()
    thread_config = {
        "configurable": {
            "thread_id": request_id,
        }
    }
    current_state = await creative_workflow.aget_state(thread_config)


    if current_state.next:
        response = StatusResponse(
            processing_status=ProcessingStatus.BUILDING,
            processing_node=current_state.next[0],
        )
    else:
        response = StatusResponse(processing_status=ProcessingStatus.COMPLETE)

    return response


@app.get("/get_creative_plan/{request_id}", 
    response_model=CreativeResultResponse,
    summary="Get completed creative plan",
    description="Retrieves the final creative assets including the generated image URL.",
    response_description="Returns the signed URL for accessing the generated creative image"
)
async def get_creative_plan(request_id: str):
    """Get the final creative plan result"""
    thread_config = {
        "configurable": {
            "thread_id": request_id,
        }
    }
    
    try:
        state = await creative_workflow.aget_state(thread_config)
        if not state:
            raise HTTPException(status_code=404, detail="Request ID not found")
        
        # Get the text-layered image path from the state
        image_path = state.values.get("generated_image_path")
        if not image_path:
            raise HTTPException(status_code=404, detail="Creative plan not ready yet")
            
        # Get the output image path from the same directory
        output_path = os.path.join(os.path.dirname(image_path), "output.png")
        if not os.path.exists(output_path):
            raise HTTPException(status_code=404, detail="Creative plan not ready yet")
            
        # Read the image file
        with open(output_path, 'rb') as f:
            image_data = f.read()
            
        # Generate a unique blob name
        generation_id = f"{uuid.uuid4()}"
        blob_name = f"image_gen_agents/{generation_id}/output.jpeg"
        
        # Save the image to storage and get the URL
        image_url = save_image(image_data, blob_name)
        
        # Generate signed URL
        signed_url = get_signed_url(blob_name)
        if not signed_url:
            raise HTTPException(status_code=500, detail="Failed to generate signed URL")
            
        return CreativeResultResponse(signed_url=signed_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/determine_objective", 
    response_model=CampaignObjectiveResponse,
    summary="Determine campaign objective",
    description="Analyzes brand information, website content, and campaign content to determine the most appropriate campaign objective.",
    response_description="Returns the selected campaign objective and reasoning"
)
async def determine_objective(request: CampaignObjectiveRequest) -> CampaignObjectiveResponse:
    try:
        # Convert Pydantic model to dict and log the data
        input_data = request.model_dump()
        logger.info(f"Input data: {input_data}")
        
        # Create thread config
        thread_id = str(uuid.uuid4())
        thread_config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
        
        # Create initial state
        state = {
            "brand_name": input_data.get("brand_name"),
            "brand_description": input_data.get("brand_description"),
            "website_url": input_data.get("website_url"),
            "campaign_url": input_data.get("campaign_url"),
            "user_prompt": input_data.get("user_prompt"),
            "campaign_objective": None,
            "reasoning": ""
        }
        
        # Run the graph
        result = await objective_workflow.ainvoke(state, config=thread_config)
        
        # Access values through the state object
        return CampaignObjectiveResponse(
            campaign_objective=result["campaign_objective"],
            reasoning=result["reasoning"]
        )
    except Exception as e:
        logger.error(f"Error in determine_objective: {str(e)}")
        logger.error(f"Input data type: {type(input_data)}")
        logger.error(f"Input data keys: {input_data.keys() if isinstance(input_data, dict) else 'Not a dict'}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
