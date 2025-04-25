from typing import Annotated, Dict, List
from langgraph.graph import MessagesState


class State(MessagesState):
    """State class for creative planner workflow"""
    
    age_group: Annotated[str, "Target demographic age range (e.g. '18-24', '25-34', '35-44')"]
    brand_description: Annotated[str, "Comprehensive description of the brand's identity, values and market positioning"]
    brand_name: Annotated[str, "Official registered name of the brand or company"]
    campaign_objective: Annotated[str, "Primary marketing goal (e.g. 'Brand Awareness', 'Lead Generation', 'Sales Conversion')"]
    gender: Annotated[str, "Target audience gender identity ('Male', 'Female', 'All')"]
    industry: Annotated[str, "Business sector or market category (e.g. 'Retail', 'Technology', 'Healthcare')"]
    interests: Annotated[List[str], "Specific hobbies, activities and topics that appeal to the target audience"]
    locations: Annotated[List[str], "Geographic targeting areas including cities, regions or countries"]
    campaign_name: Annotated[str, "A unique campaign identifier combining brand, timing, audience, and theme elements"]
    psychographic_traits: Annotated[List[str], "Psychological and behavioral characteristics of target audience"]
    product_description: Annotated[str, "Detailed explanation of product features, benefits and unique selling points"]
    product_name: Annotated[str, "Specific name or model of the product being advertised"]
    website: Annotated[str, "Full URL of the brand's or product's landing page"]
    integrated_ad_platforms: Annotated[List[str], "Digital advertising platforms where campaigns will run"]
    recommended_ad_platforms: Annotated[List[str], "Recommended Digital advertising platforms integrated with the platform"]
    campaign_start_date: Annotated[str, "Starting date of the marketing campaign (format: YYYY-MM-DD)"]
    campaign_end_date: Annotated[str, "Ending date of the marketing campaign (format: YYYY-MM-DD)"]
    total_budget: Annotated[float, "The total daily budget predicted to run a campaign based on the previous outputs"]
    channel_budget_allocation: Annotated[Dict[str, float], "A dictionary with the recommended channel names as keys and their respective daily budget allocations"]
    system_prompt: Annotated[str, "Generated creative prompts for the campaign"]
    generated_image_path: Annotated[str, "Path to the generated image file"]
    initial_prompt: Annotated[str, "Initial prompt used for image generation"]
    image_prompt: Annotated[str, "Final prompt used for image generation"]
    image_analysis: Annotated[str, "Analysis of the generated image"]
    generated_mask_path: Annotated[str, "Path to the generated mask file"]
    headline: Annotated[str, "Generated headline for the ad"]
    subheadline: Annotated[str, "Generated subheadline for the ad"]
    cta: Annotated[str, "Generated call-to-action text"] 