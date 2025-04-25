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
        self.alison_timeout = config.get("alison_timeout", 120.0)
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
            logger.info("Starting image analysis...")
            logger.info(f"Current state keys: {list(state.keys())}")
            logger.info(f"State contents: {state}")
            
            # Get the image path from state
            image_path = state.get("generated_image_path")
            if not image_path:
                logger.error("No image path found in state")
                logger.error(f"Available state keys: {list(state.keys())}")
                return state

            # Get the category from state
            category = state.get("industry")
            if not category:
                logger.error("No industry/category found in state")
                return state

            # Analyze the image
            analysis_result = await self._analyze_image(category, image_path)
            if "error" in analysis_result:
                logger.warning(f"Image analysis failed: {analysis_result['error']}")
                return state

            # Check if regeneration is needed
            combined_similarity = float(
                analysis_result.get("comparison_results", {})
                .get("overall_metrics", {})
                .get("combined_similarity", 0)
            )

            if combined_similarity >= self.analysis_threshold:
                logger.info("Image meets quality threshold, no regeneration needed")
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
            return state

        except Exception as e:
            logger.error(f"Error in image analysis process: {str(e)}")
            return state

    async def _analyze_image(self, category: str, image_path: str) -> Dict[str, Any]:
        """Analyze the image using the Alison service"""
        try:
            async with httpx.AsyncClient(timeout=self.alison_timeout) as client:
                with open(image_path, "rb") as img:
                    files = {"image": (os.path.basename(image_path), img, "application/octet-stream")}
                    response = await client.post(
                        self.alison_endpoint,
                        params={
                            "category": category,
                            "mask_threshold": self.mask_threshold,
                            "timeout": self.timeout
                        },
                        files=files
                    )
                response.raise_for_status()
                return response.json()
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