import os
import tempfile
from typing import Optional, Dict, Any

import torch
import numpy as np
from PIL import Image
from transformers import AutoProcessor, CLIPSegForImageSegmentation
from langchain_core.runnables.config import RunnableConfig
import logging

from creative_planner.agents.base.process import BaseProcessNode
from creative_planner.state import State
from creative_planner.utils.error_handler import NyxAIException
from creative_planner.utils import get_required_env_var

logger = logging.getLogger("creative_planner.agents.mask_generator")

# Set deterministic behavior for reproducibility
torch.manual_seed(int(get_required_env_var("SEED", "42")))
np.random.seed(int(get_required_env_var("SEED", "42")))
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False


class MaskGenerator(BaseProcessNode):
    """Process implementation for mask generator agent"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._load_model()

    def _load_model(self):
        """Load the CLIPSeg model and processor"""
        try:
            self.MODEL_NAME = "CIDAS/clipseg-rd64-refined"
            # Load processor with the correct config file
            self.processor = AutoProcessor.from_pretrained(
                self.MODEL_NAME
            )
            # Load model
            self.model = CLIPSegForImageSegmentation.from_pretrained(
                self.MODEL_NAME
            )
            # Move model to appropriate device
            # self.model = self.model.to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))
        except Exception as e:
            logger.exception("Error loading CLIPSeg model or processor")
            raise NyxAIException(
                internal_code=7109,
                message="Error loading config or model for segmentation",
                detail=f"7109: {str(e)}"
            )

    async def _generate_mask(
        self,
        image_path: str,
        threshold: float,
        text_prompt: Optional[str] = "background",
        model_name: Optional[str] = "mask",
        save_format: Optional[str] = "PNG"
    ) -> str:
        """
        Generates a binary segmentation mask for a given image and text prompt.
        """
        logger.info(f"Generating mask for prompt '{text_prompt}' on image: {image_path}")

        try:
            # Load and preprocess image
            image = Image.open(image_path).convert("RGB")
            orig_w, orig_h = image.size
            inputs = self.processor(text=[text_prompt], images=[image], padding=True, return_tensors="pt")
        except FileNotFoundError:
            logger.exception(f"Image not found: {image_path}")
            raise NyxAIException(
                internal_code=7102,
                message="Image file not found",
                detail=f"7102: File '{image_path}' not found."
            )
        except Exception as e:
            logger.exception("Error preparing image or processor input")
            raise NyxAIException(
                internal_code=7101,
                message="Failed to preprocess image for segmentation",
                detail=f"7101: {str(e)}"
            )

        try:
            # Inference
            with torch.no_grad():
                outputs = self.model(**inputs)

            # Post-processing
            
            probs = outputs.logits.unsqueeze(1).sigmoid()[0, 0].cpu().numpy()
            mask = (probs < threshold).astype(np.uint8)

            mask_img = Image.fromarray((mask * 255).astype(np.uint8))
            mask_resized = mask_img.resize((orig_w, orig_h), resample=Image.NEAREST)

            tmpdir = tempfile.mkdtemp(prefix=f"{model_name.lower().replace(' ', '_')}_")
            filename = os.path.splitext(os.path.basename(image_path))[0] + f"_mask.{save_format.lower()}"
            out_path = os.path.join(tmpdir, filename)
            mask_resized.save(out_path, format=save_format.upper())
            
            logger.info(f"Image at: {image_path}")

            logger.info(f"Mask saved at: {out_path}")
            return out_path

        except Exception as e:
            logger.exception("Error during mask generation process")
            raise NyxAIException(
                internal_code=7104,
                message="Error analyzing image",
                detail=f"7104: {str(e)}"
            )

    async def process(self, state: Dict[str, Any], config: RunnableConfig = None) -> Dict[str, Any]:
        """
        Process the state to generate a mask for the image.

        Args:
            state: Current state containing the image path
            config: Optional configuration for the runnable

        Returns:
            Dict[str, Any]: Updated state with the mask path
        """
        logger.info("\n" + "="*80)
        logger.info("🚀 STARTING MASK GENERATOR AGENT")
        logger.info("="*80)
        logger.info("📊 Initial State:")
        for key, value in state.items():
            logger.info(f"  - {key}: {value}")
        logger.info("="*80 + "\n")

        logger.info("Starting mask generation...")
        
        try:
            # Get the image path from state
            image_path = state.get("generated_image_path")
            if not image_path:
                raise NyxAIException(
                    internal_code=7103,
                    message="No image path found in state",
                    detail="7103: generated_image_path not found in state"
                )

            # Get threshold from environment variable
            threshold = float(get_required_env_var("MASK_THRESHOLD", "0.3"))
            logger.info(f"Threshold: {threshold}")

            # Generate mask
            mask_path = await self._generate_mask(
                image_path=image_path,
                threshold=threshold,
                text_prompt="background",
                model_name="mask",
                save_format="PNG"
            )

            # Update state with mask path
            state["generated_mask_path"] = mask_path
            logger.info(f"Mask path in state: {mask_path}")

            logger.info("Mask generated successfully")
            
            logger.info("\n" + "="*80)
            logger.info("✅ COMPLETED MASK GENERATOR AGENT")
            logger.info("="*80)
            logger.info("📊 Final State:")
            for key, value in state.items():
                logger.info(f"  - {key}: {value}")
            logger.info("="*80 + "\n")
            
            return state

        except Exception as e:
            logger.exception("Error in mask generation process")
            logger.error("\n" + "="*80)
            logger.error("❌ ERROR IN MASK GENERATOR AGENT")
            logger.error("="*80)
            logger.error("📊 Error State:")
            for key, value in state.items():
                logger.error(f"  - {key}: {value}")
            logger.error("="*80 + "\n")
            raise NyxAIException(
                internal_code=7105,
                message="Error generating mask",
                detail=f"7105: {str(e)}"
            ) 