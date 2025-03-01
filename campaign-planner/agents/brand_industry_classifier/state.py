from typing import Annotated, Optional
from langgraph.graph import MessagesState


class LocalState(MessagesState):
    brand_description: Annotated[str, "Description of the brand"]
    brand_name: Annotated[str, "Name of the brand"]
    industry: Optional[Annotated[str, "Type of Industry"]]
    product_description: Optional[Annotated[str, "Description of the product"]]
    product_name: Optional[Annotated[str, "Name of the product"]]
    website: Optional[Annotated[str, "product/brand webpage"]]
