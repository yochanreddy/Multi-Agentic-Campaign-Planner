from typing import Optional
from pydantic import BaseModel, Field


class InputSchema(BaseModel):
    brand_name: str = Field(..., description="Name of Brand")
    brand_description: str = Field(..., description="Description of Brand")
    product_name: Optional[str] = Field(default="", description="Product of Brand")
    product_description: Optional[str] = Field(
        default="", description="Description of Product"
    )
    website: Optional[str] = Field(default="", description="Website of Brand")

    class Config:
        extra = "allow"


class OutputSchema(BaseModel):
    industry: str = Field(..., description="Classified Industry Type")
