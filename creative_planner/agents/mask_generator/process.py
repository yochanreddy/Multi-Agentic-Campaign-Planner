import os
import tempfile
from typing import Optional, Dict, Any

import torch
import numpy as np
from PIL import Image
from transformers import AutoProcessor, CLIPSegForImageSegmentation
from langchain_core.runnables.config import RunnableConfig

from creative_planner.agents.base.process import BaseProcessNode
from creative_planner.state import State
from creative_planner.utils.error_handler import NyxAIException
from creative_planner.utils.logger import setup_logger
from creative_planner.utils.config import config

logger = setup_logger("mask_generator")

# Set deterministic behavior for reproducibility
torch.manual_seed(config.seed)
np.random.seed(config.seed)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False


class MaskGenerator(BaseProcessNode):
    """Process implementation for mask generator agent"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, model_name="clipseg")
        self.config = config  # Store the config parameter
        self._load_model()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def _load_model(self):
        """Load the CLIPSeg model and processor"""
        try:
            self.MODEL_NAME = "CIDAS/clipseg-rd64-refined"
            self.processor = AutoProcessor.from_pretrained(self.MODEL_NAME)
            self.model = CLIPSegForImageSegmentation.from_pretrained(self.MODEL_NAME)
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
        The mask will be in RGB format with only black (0,0,0) and white (255,255,255) pixels.
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
            
            # Create binary mask with strict thresholding
            mask = (probs < threshold).astype(np.uint8) * 255
            
            # Handle different mask shapes
            if len(mask.shape) == 1:
                # For 1D array, reshape to square
                size = int(np.sqrt(mask.shape[0]))
                if size * size != mask.shape[0]:
                    logger.warning(f"Mask size {mask.shape[0]} is not a perfect square, padding to next square")
                    size = int(np.ceil(np.sqrt(mask.shape[0])))
                    padded_size = size * size
                    mask = np.pad(mask, (0, padded_size - mask.shape[0]), mode='constant', constant_values=0)
                mask = mask.reshape(size, size)
            elif len(mask.shape) > 2:
                # For higher dimensions, take the last two dimensions
                mask = mask.reshape(mask.shape[-2], mask.shape[-1])
            
            # Create RGB mask with only black and white pixels
            mask_rgb = np.zeros((mask.shape[0], mask.shape[1], 3), dtype=np.uint8)
            mask_rgb[mask == 0] = [255, 255, 255]  # Background is white
            mask_rgb[mask == 255] = [0, 0, 0]      # Foreground is black
            
            # Create mask image and resize
            mask_img = Image.fromarray(mask_rgb)
            mask_resized = mask_img.resize((orig_w, orig_h), resample=Image.NEAREST)
            
            # Verify the mask contains only black and white pixels
            mask_array = np.array(mask_resized)
            unique_colors = np.unique(mask_array.reshape(-1, 3), axis=0)
            if len(unique_colors) > 2:
                logger.warning("Mask contains non-binary colors, forcing to black and white")
                mask_array = np.where(mask_array > 127, 255, 0).astype(np.uint8)
                mask_resized = Image.fromarray(mask_array)

            # Save the mask
            tmpdir = tempfile.mkdtemp(prefix=f"{model_name.lower().replace(' ', '_')}_")
            filename = os.path.splitext(os.path.basename(image_path))[0] + f"_mask.{save_format.lower()}"
            out_path = os.path.join(tmpdir, filename)
            mask_resized.save(out_path, format=save_format.upper())

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
        logger.info("Starting mask generation...")
        logger.info(f"Current state keys: {list(state.keys())}")

        try:
            # Get the image path from state
            image_path = state.get("generated_image_path")
            if not image_path:
                raise NyxAIException(
                    internal_code=7103,
                    message="No image path found in state",
                    detail="7103: generated_image_path not found in state"
                )

            # Get threshold from config
            threshold = float(self.config.get("mask_threshold", 0.3))

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
            return state

        except Exception as e:
            logger.exception("Error in mask generation process")
            raise NyxAIException(
                internal_code=7105,
                message="Error generating mask",
                detail=f"7105: {str(e)}"
            ) 