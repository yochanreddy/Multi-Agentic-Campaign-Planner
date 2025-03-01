from typing import Annotated, Optional
from langgraph.graph import MessagesState


class LocalState(MessagesState):
    brand_description: Annotated[str, "Description of the brand"]
    brand_name: Annotated[str, "Name of the brand"]
    campaign_objective: Annotated[str, "Objective of the campaign"]
    industry: Optional[Annotated[str, "Type of Industry"]]
