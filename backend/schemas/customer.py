from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class CustomerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150, description="Customer Full Name", examples=["John Doe"])
    phone: Optional[str] = Field(None, max_length=50, description="Contact Phone Number", examples=["+1-555-0199"])
    email: Optional[str] = Field(None, max_length=150, description="Customer Email Address", examples=["john@example.com"])


class CustomerCreate(CustomerBase):
    loyalty_points: Optional[int] = Field(0, ge=0)


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=150)
    loyalty_points: Optional[int] = Field(None, ge=0)


class CustomerOut(CustomerBase):
    id: int
    loyalty_points: int
    created_at: datetime
    updated_at: datetime
    total_sales_count: Optional[int] = 0
    total_spend: Optional[float] = 0.0

    model_config = ConfigDict(from_attributes=True)
