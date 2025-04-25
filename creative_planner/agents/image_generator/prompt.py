from typing import Dict, Any
import yaml
import os
from creative_planner.utils import get_module_logger
from langchain_core.prompts import PromptTemplate

logger = get_module_logger(__name__)

class ImageGeneratorPrompt:
    """Class for handling image generation prompt templates"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the image generator prompt.

        Args:
            config (Dict[str, Any]): Configuration dictionary
        """
        self.config = config
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> PromptTemplate:
        """
        Load the prompt template from the YAML file.

        Returns:
            PromptTemplate: The prompt template
        """
        try:
            prompt_file = os.path.join(
                os.path.dirname(__file__),
                "prompt.yaml"
            )
            with open(prompt_file, "r") as f:
                prompt_data = yaml.safe_load(f)
                return PromptTemplate.from_template(prompt_data["template"])
        except Exception as e:
            logger.error(f"Error loading prompt template: {str(e)}")
            raise

    def get_prompt(self) -> str:
        """
        Get the prompt template.

        Returns:
            str: The prompt template string
        """
        return self.prompt_template.template 