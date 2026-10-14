from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class SaleItemCreate(BaseModel):
    product_id: int = Field(..., gt=0, description="Product ID to purchase")
    quantity: int = Field(..., gt=0, description="Quantity to purchase", examples=[2])
    unit_price: Optional[float] = Field(None, ge=0.0, description="Override unit price if discount applied at item level, else uses product sale price")


class SaleItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    cost_price: float
    subtotal: float
    product_name: Optional[str] = None
    product_sku: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CheckoutRequest(BaseModel):
    customer_id: Optional[int] = Field(None, description="Registered Customer ID or null for Walk-in")
    items: List[SaleItemCreate] = Field(..., min_length=1, description="List of items in cart")
    discount: float = Field(0.0, ge=0.0, description="Fixed discount amount deducted from subtotal")
    tax_rate: float = Field(0.05, ge=0.0, le=1.0, description="Applicable tax rate (e.g. 0.05 = 5%)")
    payment_method: str = Field("Cash", description="Payment method: Cash, Card, Digital Transfer", examples=["Cash"])
    notes: Optional[str] = Field(None, max_length=500, description="Optional sale receipt notes")


class SaleOut(BaseModel):
    id: int
    invoice_no: str
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    subtotal: float
    discount: float
    tax: float
    total_amount: float
    payment_method: str
    status: str
    notes: Optional[str] = None
    created_at: datetime
    items: List[SaleItemOut] = []

    model_config = ConfigDict(from_attributes=True)


class SaleReceipt(BaseModel):
    sale: SaleOut
    items_count: int
    points_earned: int = 0
