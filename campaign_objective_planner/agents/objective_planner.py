from typing import Dict, Any, List
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from ..state import  CampaignObjective
from ..utils.scraper import URLScraper
import os
from dotenv import load_dotenv
import logging
from pydantic import BaseModel, Field
import traceback
from concurrent.futures import ThreadPoolExecutor

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class ObjectiveResponse(BaseModel):
    """Response model for the LLM's objective determination."""
    objective: CampaignObjective = Field(
        description="The selected campaign objective from the available options"
    )
    reasoning: str = Field(
        description="Explanation of why this objective was selected"
    )

class ObjectivePlannerAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        self.scraper = URLScraper()
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a marketing strategist who determines the most appropriate campaign objective. Choose the best option from:

            {campaign_objectives}

            Follow this priority order:
            1. User's Campaign Goals ({user_prompt}) - This is the most important factor
            2. Campaign URL and Campaign Content - Look for:
               - Social media URLs → Engagement
               - App Store/Play Store URLs → App Install
               - Shopping/checkout pages → Shopping
               - Form submissions → Lead Generation
               - Video content → Video Views
            3. Brand Details - Use as supporting context

            Respond with a JSON object in this format:
            {{"objective": "selected_objective", "reasoning": "explanation for the choice"}}"""),
            ("human", """Brand Name: {brand_name}
            Brand Description: {brand_description}
            User's Campaign Goals: {user_prompt}
            
            Campaign URL: {campaign_url}
            Campaign Content (Primary Focus):
            {campaign_content}
            
            Website Content (Supporting Context):
            {website_content}
            
            Please determine the most appropriate campaign objective, using the user's prompt if available.""")
        ])

    def _format_campaign_objectives(self) -> str:
        """Format campaign objectives for the prompt."""
        objectives = []
        for objective in CampaignObjective:
            objectives.append(f"- {objective.value}")
        return "\n".join(objectives)

    def _analyze_website(self, website_url: str, campaign_url: str = None) -> Dict[str, str]:
        """Get website and campaign content using the scraper in parallel."""
        def scrape_url(url: str) -> Dict[str, str]:
            logger.info(f"Getting content: {url}")
            result = self.scraper.scrape(url)
            if result['error']:
                logger.error(f"Error getting content: {result['error']}")
                return f"Error accessing {url}: {result['error']}"
            return result['content']
        
        # Create list of URLs to scrape
        urls_to_scrape = [website_url]
        if campaign_url:
            urls_to_scrape.append(campaign_url)
            
        # Scrape URLs in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(scrape_url, urls_to_scrape))
            
        # Assign results
        website_content = results[0]
        campaign_content = results[1] if len(results) > 1 else "No campaign content provided"
        
        return {
            'website_content': website_content,
            'campaign_content': campaign_content
        }

    def process(self, state: Dict) -> Dict:
        """Process the state and determine the campaign objective."""
        try:
            logger.info("Starting objective planner process")
            logger.info(f"Input state: {state}")
            
            # Get website and campaign content
            logger.info("Getting content")
            content = self._analyze_website(
                state["website_url"],
                state.get("campaign_url")
            )
            
            # Prepare prompt
            logger.info("Preparing prompt")
            campaign_objectives = self._format_campaign_objectives()
            
            # If scraping failed, note it in the content
            website_content = content['website_content']
            campaign_content = content['campaign_content']
            
            if content['website_content'].startswith('Error'):
                website_content = f"Note: Could not access website content. {content['website_content']}"
            if content['campaign_content'].startswith('Error'):
                campaign_content = f"Note: Could not access campaign content. {content['campaign_content']}"
            
            messages = self.prompt.format_messages(
                campaign_objectives=campaign_objectives,
                brand_name=state["brand_name"],
                brand_description=state["brand_description"],
                user_prompt=state.get("user_prompt", "No specific goals provided"),
                campaign_url=state.get("campaign_url", "No campaign URL provided"),
                website_content=website_content,
                campaign_content=campaign_content
            )
            logger.info("Prompt prepared successfully")
            
            # Get response from LLM
            logger.info("Invoking LLM")
            try:
                response = self.llm.invoke(messages)
                logger.info(f"LLM Response: {response}")
                
                # Clean up the response content by removing markdown code block
                content = response.content
                if content.startswith('```json'):
                    content = content[7:]  # Remove ```json
                if content.endswith('```'):
                    content = content[:-3]  # Remove ```
                content = content.strip()  # Remove any extra whitespace
                
                # Parse the response as JSON
                import json
                result = json.loads(content)
                logger.info(f"Parsed result: {result}")
                
                # Validate the result
                validated_result = ObjectiveResponse(**result)
                logger.info(f"Validated result: {validated_result}")
                
                # Store objective as string
                state["campaign_objective"] = validated_result.objective
                state["reasoning"] = validated_result.reasoning
                logger.info(f"Updated state: {state}")
                
            except Exception as llm_error:
                logger.error(f"LLM invocation error: {str(llm_error)}")
                # If LLM fails, make a best-effort determination based on available info
                if "user_prompt" in state and state["user_prompt"]:
                    # Try to determine objective from user prompt
                    if any(word in state["user_prompt"].lower() for word in ["awareness", "aware", "recognize"]):
                        state["campaign_objective"] = "Brand Awareness"
                    elif any(word in state["user_prompt"].lower() for word in ["lead", "contact", "sign up"]):
                        state["campaign_objective"] = "Lead Generation"
                    elif any(word in state["user_prompt"].lower() for word in ["shop", "buy", "purchase", "sale"]):
                        state["campaign_objective"] = "Shopping"
                    else:
                        state["campaign_objective"] = "Traffic"
                    state["reasoning"] = f"Determined objective based on user prompt: {state['user_prompt']}"
                else:
                    state["campaign_objective"] = "Traffic"
                    state["reasoning"] = "Unable to determine specific objective. Defaulting to Traffic."
            
            return state
            
        except Exception as e:
            logger.error(f"Error in objective planner process: {str(e)}")
            logger.error(f"Error traceback: {traceback.format_exc()}")
            state["campaign_objective"] = "Traffic"
            state["reasoning"] = "Unable to determine specific objective. Defaulting to Traffic."
            return state 