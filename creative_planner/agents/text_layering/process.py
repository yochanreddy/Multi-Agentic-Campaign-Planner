from typing import Dict, Any
from creative_planner.agents.base.process import BaseProcessNode
import os
import requests
from creative_planner.utils import get_required_env_var
import logging
from creative_planner.utils.logging_config import configure_logging
from creative_planner.utils.error_handler import NyxAIException
from creative_planner.agents.base.process import RunnableConfig

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
    # Get API credentials and configuration
    url = get_required_env_var("IDEOGRAM_OVERLAY_URL", "https://api.ideogram.ai/edit")
    api_key = get_required_env_var("IDEOGRAM_KEY")
    model = get_required_env_var("IDEOGRAM_MODEL", "V_2")
    
    
    # Prepare files and data
    with open(image_path, "rb") as img, open(mask_path, "rb") as mask:
        files = {
            "image_file": (os.path.basename(image_path), img, "image/jpeg"),
            "mask": (os.path.basename(mask_path), mask, "image/png")
        }
        data = {
            "prompt": prompt,
            "model": model
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
        """
        Initialize the text layering process.

        Args:
            config (Dict[str, Any]): Configuration dictionary
        """
        super().__init__(config)
        self.logger = logger

    async def process(self, state: Dict[str, Any], config: RunnableConfig = None) -> Dict[str, Any]:
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

            # Format the text overlay prompt
            overlay_prompt = f"Add only the following text within the double quotes, directly onto the image, with no background, no box, no shadow, and no extra design elements:\nHeadline: \"{headline}\"\nSubheadline: \"{subheadline or ''}\"\nCTA: \"{cta}\"\nOnly include this text. Do not add any other characters, words, or symbols, Leave the rest of the space blank."
            
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