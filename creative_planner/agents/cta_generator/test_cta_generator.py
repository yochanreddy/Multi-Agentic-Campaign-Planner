import asyncio
from creative_planner.agents.cta_generator.process import CTAGenerator
from creative_planner.state import State
from creative_planner.utils.config import config
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_cta_generator():
    try:
        # Create a test state with sample data
        test_state = State({
            "brand_name": "GreenGlow",
            "brand_description": "A sustainable skincare brand focused on natural ingredients",
            "product_name": "GlowEssence Hydrating Cream",
            "product_description": "A deeply hydrating cream with natural ingredients",
            "campaign_objective": "Increase online sales",
            "age_group": "25-45",
            "gender": "Female",
            "locations": "Urban areas",
            "psychographic_traits": "Health-conscious, environmentally aware",
            "interests": "Natural beauty, sustainability",
            "industry": "Beauty & Skincare",
            "website": "www.greenglow.com",
            "campaign_name": "Summer Hydration Campaign",
            "campaign_start_date": "2024-06-01",
            "campaign_end_date": "2024-08-31",
            "total_budget": "50000",
            "channel_budget_allocation": "Meta: 40%, Google: 60%",
            "integrated_ad_platforms": "Meta, Google",
            "recommended_ad_platforms": "Meta, Google"
        })

        # Create config dictionary
        test_config = {
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "model_name": "gpt-4",
            "temperature": 0.7
        }

        # Initialize the CTA generator
        cta_generator = CTAGenerator(test_config)

        # Generate CTA
        logger.info("Testing CTA generator...")
        result = await cta_generator.process(test_state, test_config)

        # Print results
        logger.info("\nGenerated Results:")
        logger.info(f"Headline: {result['headline']}")
        logger.info(f"Subheadline: {result['subheadline']}")
        logger.info(f"CTA: {result['cta']}")

    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_cta_generator()) 