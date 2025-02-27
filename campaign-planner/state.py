from typing import Annotated
from langgraph.graph import MessagesState


class state(MessagesState):
    brand_name: Annotated[str, "Name of the Brand"]
    brand_description: Annotated[str, "Description of the Brand"]  # optional
    product_name: Annotated[str, "Product of Brand"]  # optional
    product_description: Annotated[str, "Description of Product"]  # optional
    website: Annotated[str, "Website of Brand"]  # optional
    industry: Annotated[str, "Classified Industry Type"]
