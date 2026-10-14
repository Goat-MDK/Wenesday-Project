from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ProductBase(BaseModel):
    sku: str = Field(..., min_length=2, max_length=64, description="Stock Keeping Unit / Unique Code", examples=["SKU-1001"])
    name: str = Field(..., min_length=1, max_length=255, description="Product Name", examples=["Wireless Mouse"])
    category: str = Field("General", max_length=100, description="Product Category", examples=["Electronics"])
    barcode: Optional[str] = Field(None, max_length=64, description="Barcode/EAN/UPC", examples=["8934567890123"])
    cost_price: float = Field(0.0, ge=0.0, description="Wholesale/Cost price", examples=[15.00])
    sale_price: float = Field(..., ge=0.0, description="Retail selling price", examples=[25.99])
    stock_quantity: int = Field(0, ge=0, description="Current physical inventory", examples=[50])
    low_stock_threshold: int = Field(10, ge=0, description="Alert threshold for low stock", examples=[10])
    is_active: bool = Field(True, description="Whether product is active for sales")


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    sku: Optional[str] = Field(None, min_length=2, max_length=64)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=64)
    cost_price: Optional[float] = Field(None, ge=0.0)
    sale_price: Optional[float] = Field(None, ge=0.0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    low_stock_threshold: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ProductOut(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_low_stock: bool = False

    model_config = ConfigDict(from_attributes=True)


class StockCheckResponse(BaseModel):
    product_id: int
    sku: str
    name: str
    stock_quantity: int
    low_stock_threshold: int
    is_in_stock: bool
    is_low_stock: bool


class StockAdjustmentRequest(BaseModel):
    quantity_change: int = Field(..., description="Positive to add stock, negative to reduce")
    reason: Optional[str] = Field("Manual Adjustment", max_length=255)
