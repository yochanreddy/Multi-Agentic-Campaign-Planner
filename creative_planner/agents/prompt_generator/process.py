from typing import Dict, Any
import yaml
import os
from creative_planner.utils import get_module_logger
from creative_planner.agents.prompt_generator.prompt import PromptGeneratorPrompt

logger = get_module_logger(__name__)

class PromptGenerator:
    """Class for generating creative prompts."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the prompt generator.

        Args:
            config (Dict[str, Any]): Configuration dictionary
        """
        self.config = config
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> PromptGeneratorPrompt:
        """
        Load the prompt template from the YAML file.

        Returns:
            PromptGeneratorPrompt: The prompt template
        """
        try:
            prompt_file = os.path.join(
                os.path.dirname(__file__),
                "prompt.yaml"
            )
            with open(prompt_file, "r") as f:
                prompt_data = yaml.safe_load(f)
                return PromptGeneratorPrompt(**prompt_data)
        except Exception as e:
            logger.error(f"Error loading prompt template: {str(e)}")
            raise

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the current state to generate creative prompts.

        Args:
            state (Dict[str, Any]): Current state dictionary

        Returns:
            Dict[str, Any]: Updated state with generated prompts
        """
        try:
            # Format the prompt template with the state variables
            prompt = self.prompt_template.template.format(**state)
            
            # Update the state with the generated prompt
            state["system_prompt"] = prompt
            
            return state
        except Exception as e:
            logger.error(f"Error generating prompt: {str(e)}")
            raise 