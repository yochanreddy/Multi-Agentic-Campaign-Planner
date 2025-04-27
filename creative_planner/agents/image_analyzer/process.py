import os
import httpx
from typing import Any, Dict, Optional
from langchain_core.runnables import RunnableConfig
from creative_planner.agents.base.process import BaseProcessNode
from creative_planner.utils import get_module_logger, get_required_env_var
from creative_planner.agents.image_analyzer.prompt import ImageAnalyzerPrompt
import logging
from pathlib import Path
import yaml
from langchain.prompts import PromptTemplate
import requests
import tempfile

logger = logging.getLogger("creative_planner.agents.image_analyzer")

class ImageAnalyzer(BaseProcessNode):
    """Process node for analyzing and potentially regenerating images"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the image analyzer.

        Args:
            config (Dict[str, Any]): Configuration dictionary
        """
        super().__init__(config, model_name="gpt-4")
        self.prompt = ImageAnalyzerPrompt(config)
        # self.analysis_threshold = config.get("analysis_threshold", 0.4)
        self.analysis_threshold = 0.4
        self.mask_threshold = config.get("mask_threshold", 0.3)
        self.timeout = config.get("timeout", 10.0)
        self.alison_timeout = config.get("alison_timeout", 180.0)
        self.seed = config.get("seed", 42)
        self.alison_endpoint = get_required_env_var("ALISON_ANALYZE_ENDPOINT")

    async def process(self, state: Dict[str, Any], config: RunnableConfig) -> Dict[str, Any]:
        """
        Process the current state to analyze and potentially regenerate images.

        Args:
            state (Dict[str, Any]): Current state dictionary
            config (RunnableConfig): Configuration for the runnable

        Returns:
            Dict[str, Any]: Updated state with analysis results and potentially new image
        """
        try:
            logger.info("\n" + "="*80)
            logger.info("🚀 STARTING IMAGE ANALYZER AGENT")
            logger.info("="*80)
            logger.info("📊 Initial State:")
            for key, value in state.items():
                logger.info(f"  - {key}: {value}")
            logger.info("="*80 + "\n")

            logger.info("Starting image analysis...")
            logger.info(f"Current state keys: {list(state.keys())}")
            
            # Get the image path from state
            image_path = state.get("generated_image_path")
            if not image_path:
                logger.error("No image path found in state")
                logger.error(f"Available state keys: {list(state.keys())}")
                logger.error("\n" + "="*80)
                logger.error("❌ COMPLETED IMAGE ANALYZER AGENT (ERROR)")
                logger.error("="*80 + "\n")
                return state

            # Get the category from state
            category = state.get("industry")
            if not category:
                logger.error("No industry/category found in state")
                logger.error("\n" + "="*80)
                logger.error("❌ COMPLETED IMAGE ANALYZER AGENT (ERROR)")
                logger.error("="*80 + "\n")
                return state

            # Analyze the image
            analysis_result = await self._analyze_image(category, image_path)
            if "error" in analysis_result:
                logger.warning(f"Image analysis failed: {analysis_result['error']}")
                logger.error("\n" + "="*80)
                logger.error("❌ COMPLETED IMAGE ANALYZER AGENT (ERROR)")
                logger.error("="*80 + "\n")
                return state

            # Check if regeneration is needed
            combined_similarity = float(
                analysis_result.get("comparison_results", {})
                .get("overall_metrics", {})
                .get("combined_similarity", 0)
            )

            logger.info("combined_similarity: %s", combined_similarity)
            logger.info("analysis_threshold: %s", self.analysis_threshold)

            # if combined_similarity >= self.analysis_threshold:
            if combined_similarity >= 1:
                logger.info("Image meets quality threshold, no regeneration needed")
                logger.info("\n" + "="*80)
                logger.info("✅ COMPLETED IMAGE ANALYZER AGENT")
                logger.info("="*80 + "\n")
                return state
            else:
                logger.info("Image does not meet quality threshold, regenerating...")

            # Generate refined prompt
            refined_prompt = await self._generate_refined_prompt(state, analysis_result)
            
            logger.info("refined_prompt: %s", refined_prompt)
            # Regenerate image with refined prompt
            model_name = state.get("image_model", "Flux pro 1.1")
            new_image_path = await self._regenerate_image(model_name, refined_prompt)
            
            # Update state with new image path and analysis results
            logger.info("old_image_path: %s", image_path)
            state["generated_image_path"] = new_image_path
            logger.info("new_image_path: %s", new_image_path)
            state["refined_prompt"] = refined_prompt
            
            
            logger.info("Image regeneration completed successfully")

            logger.info("\n" + "="*80)
            logger.info("✅ COMPLETED IMAGE ANALYZER AGENT")
            logger.info("="*80)
            logger.info("📊 Final State:")
            for key, value in state.items():
                logger.info(f"  - {key}: {value}")
            logger.info("="*80 + "\n")

            return state

        except Exception as e:
            logger.error(f"Error in image analysis process: {str(e)}")
            logger.error("\n" + "="*80)
            logger.error("❌ COMPLETED IMAGE ANALYZER AGENT (ERROR)")
            logger.error("="*80)
            logger.error("📊 Final State:")
            for key, value in state.items():
                logger.error(f"  - {key}: {value}")
            logger.error("="*80 + "\n")
            return state

    async def _analyze_image(self, category: str, image_path: str) -> Dict[str, Any]:
        """Analyze the image using the Alison service"""
        try:
            logger.info("inital category: %s", category)
            # Use LLM to map industry to supported category
            mapping_prompt = f"""
            Map the following industry to one of these supported categories:
            ["automobiles","electronics","finance_and_banking","ecommerce","entertainment_and_media","food_and_beverages","gaming"]

            Industry to map: {category}

            Return only the mapped category name, nothing else.
            """
            
            # Get the mapped category using LLM
            response = await self.model.ainvoke(mapping_prompt)
            mapped_category = response.content.strip().lower()
            
            # Validate the mapped category
            supported_categories = [
                "automobiles", "electronics", "finance_and_banking", 
                "ecommerce", "entertainment_and_media", "food_and_beverages", 
                "gaming"
            ]
            
            if mapped_category not in supported_categories:
                logger.warning(f"LLM returned unsupported category: {mapped_category}")
                # Default to ecommerce if mapping fails
                mapped_category = "ecommerce"
            
            logger.info(f"Using mapped category: {mapped_category} (original: {category})")

            logger.info("mapped category: %s", mapped_category)
            
            # Prepare the base parameters
            params = {"category": mapped_category}
            
            # Create the client with proper timeout and redirect following
            async with httpx.AsyncClient(timeout=self.alison_timeout, follow_redirects=True) as client:
                # Check if file exists
                if not os.path.isfile(image_path):
                    logger.error(f"File '{image_path}' not found")
                    return {"error": f"File '{image_path}' not found"}

                # Open and send the image file
                with open(image_path, "rb") as img:
                    files = {"image": (os.path.basename(image_path), img, "application/octet-stream")}
                    logger.info(f"Sending request to {self.alison_endpoint}")
                    logger.info(f"Request details:")
                    logger.info(f"- Category: {mapped_category}")
                    logger.info(f"- Image file: {os.path.basename(image_path)}")
                    logger.info(f"- Content type: application/octet-stream")
                    
                    response = await client.post(
                        self.alison_endpoint,
                        params=params,
                        files=files
                    )
                
                # Log response details
                logger.info(f"Response status: {response.status_code}")
                logger.info(f"Response headers: {response.headers}")
                
                # Check response status
                response.raise_for_status()
                result = response.json()
                logger.info(f"API call successful. Response received")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error analyzing image: {str(e)}")
            logger.error(f"Response content: {e.response.text if hasattr(e, 'response') else 'No response content'}")
            return {"error": f"HTTP error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            return {"error": str(e)}

    async def _generate_refined_prompt(self, state: Dict[str, Any], analysis_result: Dict[str, Any]) -> str:
        """Generate a refined prompt based on analysis results using a message-based approach"""
        try:
            # Get recommendations from analysis result
            recommendations = analysis_result.get("recommendations", {})
            recommendation_str = str(recommendations)
            
            # Load the prompt template from prompt_generator
            prompt_file = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "prompt_generator",
                "prompt.yaml"
            )
            
            # Load the YAML config
            with open(prompt_file, "r") as f:
                prompt_config = yaml.safe_load(f)
            
            # Create a PromptTemplate from the YAML config
            prompt_template = PromptTemplate(
                template=prompt_config["template"],
                input_variables=prompt_config["input_variables"]
            )
            
            # Get the input variables from state
            input_vars = {
                var: state.get(var)
                for var in prompt_config["input_variables"]
            }
            
            # Format the prompt with the input variables
            formatted_prompt = prompt_template.format(**input_vars)
            logger.info("formatted_prompt: %s", formatted_prompt)
            
            # Create message history
            messages = [
                {"role": "system", "content": formatted_prompt},
                {"role": "assistant", "content": state.get("system_prompt", "")},
                {"role": "user", "content": recommendation_str}
            ]
            
            
            # Generate refined prompt using the model
            response = await self.model.ainvoke(messages)
            logger.info("response: %s", response)
            return response.content
        except Exception as e:
            logger.error(f"Error generating refined prompt: {str(e)}")
            raise

    async def _regenerate_image(self, model_name: str, prompt: str) -> str:
        """Regenerate the image using the specified model"""
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
            logger.error(f"Error regenerating image: {str(e)}")
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