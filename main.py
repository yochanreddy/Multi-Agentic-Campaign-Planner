import os
from typing import List, Literal
import uuid
from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.memory import MemorySaver
from psycopg_pool import AsyncConnectionPool
from pydantic import BaseModel, Field
from campaign_planner.utils import load_config, draw_mermaid_graph
from contextlib import asynccontextmanager
from campaign_planner.graph import CampaignPlanner
from enum import Enum

workflow = None
ChannelType = Literal["Meta", "Google", "LinkedIn", "TikTok"]
config = None


class ProcessingStatus(str, Enum):
    QUEUED = "QUEUED"
    BUILDING = "BUILDING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global ChannelType
    global workflow
    global config

    config = load_config()
    config["LOG_LEVEL"] = os.getenv("LOG_LEVEL", "INFO")
    ChannelType = Literal[tuple(config["AD_CHANNELS"])]
    if config["LOG_LEVEL"].lower() == "debug":
        config["checkpointer"] = MemorySaver()

        workflow = CampaignPlanner(config).get_compiled_graph()
        draw_mermaid_graph(workflow)
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
            yield


class SubmitRequest(BaseModel):
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
            }
        }


class SubmitResponse(BaseModel):
    request_id: str = Field(description="unique request id")


class StatusResponse(BaseModel):
    processing_status: str = Field(description="current processing status")
    processing_node: str = Field(description="current processing node", default="")


class ResultResponse(BaseModel):
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


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/request_campaign_plan", response_model=SubmitResponse)
async def request_campaign_plan(
    request: SubmitRequest, background_tasks: BackgroundTasks
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


@app.get("/status_campaign_plan/{request_id}", response_model=StatusResponse)
async def status_campaign_plan(request_id: str) -> StatusResponse:
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


@app.get("/get_campaign_plan/{request_id}", response_model=ResultResponse)
async def get_campaign_plan(request_id: str) -> ResultResponse:
    thread_config = {
        "configurable": {
            "thread_id": request_id,
        }
    }
    current_state = await workflow.aget_state(thread_config)

    return ResultResponse.model_validate(current_state.values)
