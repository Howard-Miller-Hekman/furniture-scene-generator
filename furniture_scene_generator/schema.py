"""
Pydantic schemas for furniture scene generator.
"""

from typing import Optional, TypedDict

from pydantic import BaseModel, Field, HttpUrl
from decimal import Decimal

from langchain_core.messages import HumanMessage, AIMessage


class ProductData(BaseModel):
    """Schema for product data with inventory and pricing information."""

    model: str = Field(
        ...,
        description="Product model identifier or SKU"
    )

    qoh: Optional[int] = Field(
        None,
        description="Quantity on hand (inventory)",
        ge=0
    )

    wl: Optional[str] = Field(
        None,
        description="WL Id",
    )

    retail: Optional[Decimal] = Field(
        None,
        description="Retail price",
        ge=0
    )

    map: Optional[Decimal] = Field(
        None,
        alias="MAP",
        description="Minimum Advertised Price",
        ge=0
    )

    cost: Optional[Decimal] = Field(
        None,
        description="Cost price",
        ge=0
    )

    landed_cost: Optional[Decimal] = Field(
        None,
        description="Landed cost including shipping and duties",
        ge=0
    )

    silo_image: Optional[str] = Field(
        None,
        description="URL to product silo image (isolated on white background)"
    )

    website_link_for_context: Optional[str] = Field(
        None,
        description="Website URL for additional product context"
    )

    lifestyle_image: Optional[str] = Field(
        None,
        description="URL to lifestyle image showing product in context"
    )

    comment: Optional[str] = Field(
        None,
        description="Comment"
    )

    edited_image: Optional[str] = Field(
        None,
        description="Edited Image"
    )

    class Config:
        """Pydantic model configuration."""
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "model": "SOF-12345",
                "qoh": 15,
                "wl": 3,
                "retail": "1299.99",
                "MAP": "1099.99",
                "cost": "649.50",
                "landed_cost": "725.00",
                "silo_image": "https://example.com/images/sof-12345-silo.jpg",
                "website_link_for_context": "https://example.com/products/sof-12345",
                "lifestyle_image": "https://example.com/images/sof-12345-lifestyle.jpg"
            }
        }


class ImageEditState(TypedDict):
    original_prompt: str
    improved_prompt: str
    product_data: ProductData
    response: Optional[AIMessage]
    error: Optional[str]
    source_image_data: Optional[bytes]
    source_image_mime_type: Optional[str]
    target_width: Optional[int]
    target_height: Optional[int]
