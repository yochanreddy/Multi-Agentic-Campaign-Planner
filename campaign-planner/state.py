from typing import Annotated, List
from langgraph.graph import MessagesState


class State(MessagesState):
    age_group: Annotated[
        str, "Target demographic age range (e.g. '18-24', '25-34', '35-44')"
    ]
    brand_description: Annotated[
        str,
        "Comprehensive description of the brand's identity, values and market positioning",
    ]
    brand_name: Annotated[str, "Official registered name of the brand or company"]
    campaign_objective: Annotated[
        str,
        "Primary marketing goal (e.g. 'Brand Awareness', 'Lead Generation', 'Sales Conversion')",
    ]
    gender: Annotated[str, "Target audience gender identity ('Male', 'Female', 'All')"]
    industry: Annotated[
        str,
        "Business sector or market category (e.g. 'Retail', 'Technology', 'Healthcare')",
    ]
    interests: Annotated[
        List[str],
        "Specific hobbies, activities and topics that appeal to the target audience",
    ]
    locations: Annotated[
        List[str], "Geographic targeting areas including cities, regions or countries"
    ]
    product_description: Annotated[
        str,
        "Detailed explanation of product features, benefits and unique selling points",
    ]
    product_name: Annotated[
        str, "Specific name or model of the product being advertised"
    ]
    psychographic_traits: Annotated[
        List[str],
        "Psychological and behavioral characteristics of target audience (e.g. 'Environmentally conscious', 'Tech-savvy', 'Health-oriented')",
    ]
    website: Annotated[str, "Full URL of the brand's or product's landing page"]
    integrated_ad_platforms: Annotated[
        List[str],
        "Digital advertising platforms where campaigns will run (e.g. 'Meta', 'Google', 'LinkedIn', 'TikTok')",
    ]
    recommended_ad_platforms: Annotated[
        List[str],
        "Recommended Digital advertising platforms integrated with the platform where campaigns will run",
    ]
    campaign_start_date: Annotated[
        str,
        "Starting date of the marketing campaign (format: DD-MM-YYYY)",
    ]
    campaign_end_date: Annotated[
        str,
        "Ending date of the marketing campaign (format: DD-MM-YYYY)",
    ]
