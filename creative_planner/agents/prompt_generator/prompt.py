from pydantic import BaseModel

class PromptGeneratorPrompt(BaseModel):
    """Class for managing the prompt template."""
    
    template: str
    
    def get_prompt(self) -> str:
        """
        Get the prompt template.
        
        Returns:
            str: The prompt template
        """
        return self.template 