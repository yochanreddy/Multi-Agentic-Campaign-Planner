from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from creative_planner.agents.base.process import BaseProcessNode
from creative_planner.agents.text_layering.prompt import TextLayeringPrompt
import os
import requests
import uuid
from creative_planner.utils.storage import save_image, get_signed_url
from creative_planner.utils import get_required_env_var
import logging
from creative_planner.utils.logging_config import configure_logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from creative_planner.utils.error_handler import NyxAIException
import base64
from PIL import Image
import io

# Configure logging
configure_logging()
logger = logging.getLogger("creative_planner.agents.text_layering")

def generate_image(prompt: str, image_path: str, mask_path: str) -> str:
    """
    Generate an image with text overlay using Ideogram API.
    
    Args:
        prompt (str): The text prompt describing the desired image
        image_path (str): Path to the base image
        mask_path (str): Path to the mask image
        
    Returns:
        str: Local path to the generated image
    """
    # Get API credentials
    url = "https://api.ideogram.ai/edit"
    api_key = get_required_env_var("IDEOGRAM_KEY")
    
    # Prepare files and data
    with open(image_path, "rb") as img, open(mask_path, "rb") as mask:
        files = {
            "image_file": (os.path.basename(image_path), img, "image/jpeg"),
            "mask": (os.path.basename(mask_path), mask, "image/png")
        }
        data = {
            "prompt": prompt,
            "model": "V_2",
            "negative_prompt": "text, watermark, logo, signature, writing, letters, words"
        }
        
        # Make the request
        response = requests.post(
            url,
            headers={"Api-Key": api_key},
            data=data,
            files=files
        )
        
        # Check for errors
        response.raise_for_status()
        
        # Get the image URL from the response
        result = response.json()
        image_url = result["data"][0]["url"]
        
        # Download the image
        image_response = requests.get(image_url)
        image_response.raise_for_status()
        
        # Save the image locally
        output_path = os.path.join(os.path.dirname(image_path), "output.png")
        with open(output_path, "wb") as f:
            f.write(image_response.content)
            
        return output_path

class TextLayeringProcess(BaseProcessNode):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.prompt = TextLayeringPrompt()
        self.llm = ChatOpenAI(
            model_name="gpt-4",
            temperature=0.7,
            api_key=config.get("openai_api_key")
        )
        self.logger = logger

    async def process(self, state: Dict[str, Any], config: RunnableConfig) -> Dict[str, Any]:
        try:
            logger.info("\n" + "="*80)
            logger.info("🚀 STARTING TEXT LAYERING AGENT")
            logger.info("="*80)
            logger.info("📊 Initial State:")
            for key, value in state.items():
                logger.info(f"  - {key}: {value}")
            logger.info("="*80 + "\n")

            self.logger.info("Starting text layering process...")
            self.logger.info(f"Current state keys: {list(state.keys())}")

            # Get the input values from state
            headline = state.get('headline', '')
            subheadline = state.get('subheadline', '')
            cta = state.get('cta', '')
            image_path = state.get('generated_image_path', '')
            mask_path = state.get('generated_mask_path', '')

            if not image_path:
                raise NyxAIException(
                    internal_code=7102,
                    message="No image path found in state",
                    http_status_code=500
                )
            if not mask_path:
                raise NyxAIException(
                    internal_code=7102,
                    message="No mask path found in state",
                    http_status_code=500
                )

            # Generate default text if empty
            if not headline:
                headline = "Discover Your Natural Glow"
            if not subheadline:
                subheadline = "Experience the power of nature with our organic skincare"
            if not cta:
                cta = "Shop Now"

            # Generate the prompt
            prompt = self.prompt.get_prompt(headline, subheadline, cta, image_path)

            # Get the LLM response for text styling
            response = await self.llm.ainvoke(prompt)

            # Parse the response to get text positioning and styling
            text_config = self._parse_response(response)

            # Format the text overlay prompt
            overlay_prompt = self._format_overlay_prompt(headline, subheadline, cta, text_config)
            
            self.logger.info(f"Generated overlay prompt: {overlay_prompt}")
            self.logger.info(f"Using image path: {image_path}")
            self.logger.info(f"Using mask path: {mask_path}")

            try:
                # Apply text overlay using Ideogram API
                output_path = generate_image(overlay_prompt, image_path, mask_path)
                
                # Update state with the new image path
                state['image_url'] = output_path
                self.logger.info(f"Text layered image saved to: {output_path}")
                self.logger.info("Text layering completed successfully")
                
                logger.info("\n" + "="*80)
                logger.info("✅ COMPLETED TEXT LAYERING AGENT")
                logger.info("="*80)
                logger.info("📊 Final State:")
                for key, value in state.items():
                    logger.info(f"  - {key}: {value}")
                logger.info("="*80 + "\n")
                
                return state
                
            except requests.exceptions.HTTPError as e:
                self.logger.error(f"HTTP error in text layering: {str(e)}")
                if e.response is not None:
                    self.logger.error(f"Response content: {e.response.text}")
                logger.error("\n" + "="*80)
                logger.error("❌ ERROR IN TEXT LAYERING AGENT")
                logger.error("="*80)
                logger.error("📊 Error State:")
                for key, value in state.items():
                    logger.error(f"  - {key}: {value}")
                logger.error("="*80 + "\n")
                raise NyxAIException(
                    internal_code=2006,
                    message="Error calling Ideogram API",
                    detail=f"HTTP {e.response.status_code}: {e.response.text if e.response else str(e)}",
                    http_status_code=500
                )
            except Exception as e:
                self.logger.error(f"Error in text layering: {str(e)}")
                logger.error("\n" + "="*80)
                logger.error("❌ ERROR IN TEXT LAYERING AGENT")
                logger.error("="*80)
                logger.error("📊 Error State:")
                for key, value in state.items():
                    logger.error(f"  - {key}: {value}")
                logger.error("="*80 + "\n")
                raise NyxAIException(
                    internal_code=2500,
                    message="Unexpected error in text layering",
                    detail=str(e),
                    http_status_code=500
                )

        except Exception as e:
            self.logger.error(f"Error in text layering process: {str(e)}")
            logger.error("\n" + "="*80)
            logger.error("❌ ERROR IN TEXT LAYERING AGENT")
            logger.error("="*80)
            logger.error("📊 Error State:")
            for key, value in state.items():
                logger.error(f"  - {key}: {value}")
            logger.error("="*80 + "\n")
            raise

    def _parse_response(self, response: AIMessage) -> Dict[str, Any]:
        """Parse the LLM response to extract text positioning and styling"""
        try:
            # Extract content from AIMessage
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Parse the response to extract text positioning and styling
            lines = content.split('\n')
            config = {}
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    config[key.strip()] = value.strip()
            
            # Set default values if missing
            config.setdefault('headline_color', 'white')
            config.setdefault('headline_size', '60')
            config.setdefault('headline_x', 'center')
            config.setdefault('headline_y', 'top')
            
            config.setdefault('subheadline_color', 'white')
            config.setdefault('subheadline_size', '40')
            config.setdefault('subheadline_x', 'center')
            config.setdefault('subheadline_y', 'middle')
            
            config.setdefault('cta_color', 'white')
            config.setdefault('cta_size', '50')
            config.setdefault('cta_x', 'center')
            config.setdefault('cta_y', 'bottom')
            
            return config
        except Exception as e:
            self.logger.error(f"Error parsing LLM response: {str(e)}")
            # Return default configuration if parsing fails
            return {
                'headline_color': 'white', 'headline_size': '60', 'headline_x': 'center', 'headline_y': 'top',
                'subheadline_color': 'white', 'subheadline_size': '40', 'subheadline_x': 'center', 'subheadline_y': 'middle',
                'cta_color': 'white', 'cta_size': '50', 'cta_x': 'center', 'cta_y': 'bottom'
            }

    def _format_overlay_prompt(self, headline: str, subheadline: str, cta: str, text_config: Dict[str, Any]) -> str:
        """Format the prompt for Ideogram text overlay"""
        # Combine text elements with their styling
        prompt_parts = []
        if headline:
            headline_style = f"color: {text_config.get('headline_color', 'white')}, size: {text_config.get('headline_size', '60')}"
            prompt_parts.append(f"Headline '{headline}' at position {text_config.get('headline_x', 'center')},{text_config.get('headline_y', 'top')} with {headline_style}")
        
        if subheadline:
            subheadline_style = f"color: {text_config.get('subheadline_color', 'white')}, size: {text_config.get('subheadline_size', '40')}"
            prompt_parts.append(f"Subheadline '{subheadline}' at position {text_config.get('subheadline_x', 'center')},{text_config.get('subheadline_y', 'middle')} with {subheadline_style}")
        
        if cta:
            cta_style = f"color: {text_config.get('cta_color', 'white')}, size: {text_config.get('cta_size', '50')}"
            prompt_parts.append(f"CTA '{cta}' at position {text_config.get('cta_x', 'center')},{text_config.get('cta_y', 'bottom')} with {cta_style}")
        
        # Ensure we have at least one text element
        if not prompt_parts:
            prompt_parts.append("Add a simple text overlay with the brand name")
        
        return ". ".join(prompt_parts) 