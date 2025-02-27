from typing import Optional
from pydantic import BaseModel, Field


class Input(BaseModel):
    brand_name: str = Field(..., description="Name of Brand")
    brand_description: str = Field(..., description="Description of Brand")
    website: str = Field(..., description="Website of Brand")
    product_name: Optional[str] = Field(..., description="Product of Brand")
    product_description: Optional[str] = Field(
        ..., description="Description of Product"
    )
    industry: str = Field(..., description="Classified Industry Type")
