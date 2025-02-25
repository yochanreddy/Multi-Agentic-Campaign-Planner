from typing import Type
from datetime import datetime
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class CurrentDateInput(BaseModel):
    """Input schema for CurrentDateTool."""
    pass


class CurrentDateTool(BaseTool):
    name: str = "CurrentDateTool"
    description: str = (
        "This tool is used to get the current date so that the campaign can be scheduled for the future from the current date."
    )
    args_schema: Type[BaseModel] = CurrentDateInput

    def _run(self) -> str:
        
        return datetime.now().strftime("%A, %B %d, %Y, %I:%M %p %Z")
