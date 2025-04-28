import yaml
from pathlib import Path
from typing import Dict, Any

from creative_planner.agents.base.prompt import BasePrompt


class CTAGeneratorPrompt(BasePrompt):
    """Prompt implementation for CTA generator agent"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._load_prompt_template()

    def _load_prompt_template(self):
        """Load the CTA prompt template from YAML file"""
        try:
            prompt_path = Path(__file__).parent / "prompt.yaml"
            with open(prompt_path, "r") as f:
                self.prompt_template = yaml.safe_load(f)
        except Exception as e:
            raise Exception(f"Error loading CTA prompt template: {str(e)}")

    def get_prompt(self, state: Dict[str, Any]) -> str:
        """
        Get the CTA prompt string.

        Args:
            state: Current state containing brand and campaign information

        Returns:
            str: Formatted CTA prompt
        """
        return self.prompt_template["cta_prompt"].format(**state) 