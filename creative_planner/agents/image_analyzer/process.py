import os
import httpx
from typing import Any, Dict, Optional
from langchain_core.runnables import RunnableConfig
from creative_planner.agents.base.process import BaseProcessNode
from creative_planner.utils import get_module_logger, get_required_env_var
from creative_planner.agents.image_analyzer.prompt import ImageAnalyzerPrompt

logger = get_module_logger(__name__)

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
        self.analysis_threshold = config.get("analysis_threshold", 0.4)
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
            print("\n" + "="*80)
            print("🚀 STARTING IMAGE ANALYZER AGENT")
            print("="*80)
            print("📊 Initial State:")
            for key, value in state.items():
                print(f"  - {key}: {value}")
            print("="*80 + "\n")

            logger.info("Starting image analysis...")
            logger.info(f"Current state keys: {list(state.keys())}")
            
            # Get the image path from state
            image_path = state.get("generated_image_path")
            if not image_path:
                logger.error("No image path found in state")
                logger.error(f"Available state keys: {list(state.keys())}")
                print("\n" + "="*80)
                print("❌ COMPLETED IMAGE ANALYZER AGENT (ERROR)")
                print("="*80 + "\n")
                return state

            # Get the category from state
            category = state.get("industry")
            if not category:
                logger.error("No industry/category found in state")
                print("\n" + "="*80)
                print("❌ COMPLETED IMAGE ANALYZER AGENT (ERROR)")
                print("="*80 + "\n")
                return state

            # Analyze the image
            analysis_result = await self._analyze_image(category, image_path)
            if "error" in analysis_result:
                logger.warning(f"Image analysis failed: {analysis_result['error']}")
                print("\n" + "="*80)
                print("❌ COMPLETED IMAGE ANALYZER AGENT (ERROR)")
                print("="*80 + "\n")
                return state

            # Check if regeneration is needed
            combined_similarity = float(
                analysis_result.get("comparison_results", {})
                .get("overall_metrics", {})
                .get("combined_similarity", 0)
            )

            if combined_similarity >= self.analysis_threshold:
                logger.info("Image meets quality threshold, no regeneration needed")
                print("\n" + "="*80)
                print("✅ COMPLETED IMAGE ANALYZER AGENT")
                print("="*80 + "\n")
                return state

            # Generate refined prompt
            refined_prompt = await self._generate_refined_prompt(state, analysis_result)
            
            # Regenerate image with refined prompt
            model_name = state.get("image_model", "Flux pro 1.1")
            new_image_path = await self._regenerate_image(model_name, refined_prompt)
            
            # Update state with new image path and analysis results
            state["generated_image_path"] = new_image_path
            state["refined_prompt"] = refined_prompt
            state["analysis_result"] = analysis_result
            state["analysis_metrics"] = {
                "combined_similarity": combined_similarity,
                "mask_threshold": self.mask_threshold,
                "analysis_threshold": self.analysis_threshold
            }
            
            logger.info("Image regeneration completed successfully")

            print("\n" + "="*80)
            print("✅ COMPLETED IMAGE ANALYZER AGENT")
            print("="*80)
            print("📊 Final State:")
            for key, value in state.items():
                print(f"  - {key}: {value}")
            print("="*80 + "\n")

            return state

        except Exception as e:
            logger.error(f"Error in image analysis process: {str(e)}")
            print("\n" + "="*80)
            print("❌ COMPLETED IMAGE ANALYZER AGENT (ERROR)")
            print("="*80)
            print("📊 Final State:")
            for key, value in state.items():
                print(f"  - {key}: {value}")
            print("="*80 + "\n")
            return state

    async def _analyze_image(self, category: str, image_path: str) -> Dict[str, Any]:
        """Analyze the image using the Alison service"""
        try:
            # Map industry to supported category
            category_mapping = {
                "Catering and Food Services": "food_and_beverages",
                "Food Delivery": "food_and_beverages",
                "Restaurant": "food_and_beverages",
                "Retail": "ecommerce",
                "Technology": "electronics",
                "Finance": "finance_and_banking",
                "Gaming": "gaming",
                "Media": "entertainment_and_media",
                "Automotive": "automobiles"
            }
            
            # Get the mapped category or use the original if not found
            mapped_category = category_mapping.get(category, category)
            
            # Prepare the base parameters
            params = {"category": mapped_category}
            logger.info(f"Using mapped category: {mapped_category} (original: {category})")
            
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
        """Generate a refined prompt based on analysis results"""
        try:
            # Get the prompt template
            prompt_template = self.prompt.get_prompt()
            
            # Format the prompt with state values and analysis results
            formatted_prompt = prompt_template.format(
                system_prompt=state["system_prompt"],
                brand_name=state["brand_name"],
                product_name=state["product_name"],
                industry=state["industry"],
                initial_prompt=state.get("initial_prompt", ""),
                initial_image_prompt=state.get("image_prompt", ""),
                analysis_result=str(analysis_result.get("comparison_results", {})),
                recommendations=str(analysis_result.get("recommendations", {}))
            )
            
            # Generate refined prompt using the model
            response = await self.model.ainvoke(formatted_prompt)
            return response.content
        except Exception as e:
            logger.error(f"Error generating refined prompt: {str(e)}")
            raise

    async def _regenerate_image(self, model_name: str, prompt: str) -> str:
        """Regenerate the image using the specified model"""
        try:
            # This would use the same image generation logic as in the image generator
            # For now, we'll just return a placeholder
            return f"regenerated_{model_name}_{hash(prompt)}.jpg"
        except Exception as e:
            logger.error(f"Error regenerating image: {str(e)}")
            raise 