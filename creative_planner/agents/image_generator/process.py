import os
import tempfile
import requests
from typing import Any, Dict
from langchain_core.runnables import RunnableConfig
from creative_planner.agents.base.process import BaseProcessNode
from creative_planner.utils import get_required_env_var
import logging

logger = logging.getLogger("creative_planner.agents.image_generator")

class ImageGenerator(BaseProcessNode):
    """Process node for generating images from creative prompts"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the image generator.

        Args:
            config (Dict[str, Any]): Configuration dictionary
        """
        super().__init__(config)

    async def process(self, state: Dict[str, Any], config: RunnableConfig) -> Dict[str, Any]:
        """
        Process the current state to generate images from creative prompts.

        Args:
            state (Dict[str, Any]): Current state dictionary
            config (RunnableConfig): Configuration for the runnable

        Returns:
            Dict[str, Any]: Updated state with generated image paths
        """
        try:
            logger.info("\n" + "="*80)
            logger.info("🚀 STARTING IMAGE GENERATOR AGENT")
            logger.info("="*80)
            logger.info("📊 Initial State:")
            for key, value in state.items():
                logger.info(f"  - {key}: {value}")
            logger.info("="*80 + "\n")

            logger.info("Starting image generation process")
            logger.info("Generating images from creative prompts...")
            logger.info(f"Current state keys: {list(state.keys())}")
            
            # Generate the image using the specified model
            model_name = state.get("image_model", "Flux pro 1.1")
            image_path = self._download_image(model_name, state["system_prompt"])
            
            # Update state with the generated image path
            state["generated_image_path"] = image_path
            state["image_prompt"] = state["system_prompt"]
            
            logger.info(f"Updated state keys: {list(state.keys())}")
            logger.info(f"Image path in state: {state.get('generated_image_path')}")
            logger.info("Images generated successfully")

            logger.info("\n" + "="*80)
            logger.info("✅ COMPLETED IMAGE GENERATOR AGENT")
            logger.info("="*80)
            logger.info("📊 Final State:")
            for key, value in state.items():
                logger.info(f"  - {key}: {value}")
            logger.info("="*80 + "\n")

            return state
        except Exception as e:
            logger.error(f"Error in image generation: {str(e)}")
            logger.error("\n" + "="*80)
            logger.error("❌ ERROR IN IMAGE GENERATOR AGENT")
            logger.error("="*80)
            logger.error("📊 Error State:")
            for key, value in state.items():
                logger.error(f"  - {key}: {value}")
            logger.error("="*80 + "\n")
            raise Exception(f"Failed to generate images: {str(e)}")

    def _download_image(self, model_name: str, prompt: str) -> str:
        """Download image from the specified model"""
        logger.info(f"Downloading image from model: {model_name}")
        try:
            if model_name == "Flux pro 1.1":
                image_url = self._handle_flux_pro(prompt)
            elif model_name == "Reve 1.0":
                image_url = self._handle_reve(prompt)
            elif model_name == "Ideogram v2":
                image_url = self._handle_ideogram(prompt)
            else:
                raise Exception(f"Unsupported model: {model_name}")

            response = requests.get(image_url, stream=True)
            response.raise_for_status()

            tmpdir = tempfile.mkdtemp(prefix=f"{model_name.lower().replace(' ', '_')}_")
            filename = os.path.basename(image_url.split("?")[0]) or "image.jpg"
            path = os.path.join(tmpdir, filename)

            with open(path, "wb") as f:
                for chunk in response.iter_content(8192):
                    f.write(chunk)

            logger.info(f"Image saved to: {path}")
            return path

        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
            raise

    def _handle_flux_pro(self, prompt: str) -> str:
        """Handle Flux Pro 1.1 image generation"""
        url_post = get_required_env_var("FLUX_API_HOST_POST")
        url_get = get_required_env_var("FLUX_API_HOST_GET")
        headers = {
            "Content-Type": "application/json",
            "x-key": get_required_env_var("NYX_BFL_FLUX_KEY")
        }
        payload = {
            "prompt": prompt,
            "width": 1024,
            "height": 768
        }

        response = requests.post(url_post, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        image_id = data.get("id")

        if not image_id:
            raise Exception("Missing image ID in Flux Pro response")

        max_attempts = 10
        for _ in range(max_attempts):
            result = requests.get(url_get, headers=headers, params={"id": image_id})
            result.raise_for_status()
            result_data = result.json()

            status = result_data.get("status")
            if status == "Ready":
                return result_data["result"].get("sample")
            elif status not in ["Pending", "InProgress"]:
                raise Exception(f"Unexpected status: {status}")

        raise Exception("Flux Pro image generation timed out")

    def _handle_reve(self, prompt: str) -> str:
        """Handle Reve 1.0 image generation"""
        url = get_required_env_var("REVE_API_URL")
        payload = {"prompt": prompt, "negative_prompt": "..."}
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json().get("result")

    def _handle_ideogram(self, prompt: str) -> str:
        """Handle Ideogram v2 image generation"""
        url = get_required_env_var("IDEOGRAM_GENERATE_URL")
        headers = {
            "Api-Key": get_required_env_var("IDEOGRAM_KEY"),
            "Content-Type": "application/json"
        }
        payload = {
            "image_request": {
                "prompt": prompt,
                "model": "V_2",
                "style_type": "REALISTIC",
                "aspect_ratio": "ASPECT_16_9",
                "negative_prompt": "logos, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts,signature, watermark, username, blurry"
            }
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["data"][0].get("url") 