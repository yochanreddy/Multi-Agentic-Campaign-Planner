from typing import Annotated, Optional
from enum import Enum
from langgraph.graph import MessagesState

class CampaignObjective(str, Enum):
    TRAFFIC = "Traffic"
    VIDEO_VIEWS = "Video Views"
    ENGAGEMENT = "Engagement"
    LEAD_GENERATION = "Lead Generation"
    SHOPPING = "Shopping"
    WEBSITE_CONVERSION = "Website Conversion"
    BRAND_AWARENESS = "Brand Awareness"
    APP_ENGAGEMENT = "App Engagement"
    APP_INSTALL = "App Install"

class State(MessagesState):
    """State class for campaign objective planner workflow"""
    
    brand_name: Annotated[Optional[str], "Official registered name of the brand or company"]
    brand_description: Annotated[Optional[str], "Comprehensive description of the brand's identity, values and market positioning"]
    website_url: Annotated[Optional[str], "Full URL of the brand's website"]
    campaign_url: Annotated[Optional[str], "Full URL of the campaign landing page"]
    user_prompt: Annotated[Optional[str], "Optional user-provided description of the intended campaign objective or marketing goals"]
    campaign_objective: Annotated[Optional[str], "Selected campaign objective based on brand analysis"]
    reasoning: Annotated[Optional[str], "Explanation of why this objective was selected"]
