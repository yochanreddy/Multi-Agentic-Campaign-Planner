from typing import Dict, Any
import yaml
from pathlib import Path

class TextLayeringPrompt:
    def __init__(self):
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> Dict[str, Any]:
        prompt_path = Path(__file__).parent / "prompt.yaml"
        with open(prompt_path, "r") as f:
            return yaml.safe_load(f)

    def get_prompt(self, headline: str, subheadline: str, cta: str, image_path: str) -> str:
        # Create a list of text elements that are not empty
        text_elements = []
        if headline:
            text_elements.append(f"Headline: {headline}")
        if subheadline:
            text_elements.append(f"Subheadline: {subheadline}")
        if cta:
            text_elements.append(f"CTA: {cta}")

        # Join the text elements with newlines
        text_content = "\n".join(text_elements) if text_elements else "No text content provided"

        return self.prompt_template["system"].format(
            text_content=text_content,
            image_path=image_path
        ) 