from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from backend.database import get_db
from backend.models.customer import Customer
from backend.models.sale import Sale
from backend.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerOut
)

router = APIRouter(prefix="/customers", tags=["Customers"])


def _to_customer_out(c: Customer, db: Session) -> CustomerOut:
    # Compute sales count and total spend
    sales_stats = db.query(
        func.count(Sale.id),
        func.coalesce(func.sum(Sale.total_amount), 0.0)
    ).filter(Sale.customer_id == c.id, Sale.status == "COMPLETED").first()

    sales_count = sales_stats[0] if sales_stats else 0
    total_spend = float(sales_stats[1]) if sales_stats else 0.0

    return CustomerOut(
        id=c.id,
        name=c.name,
        phone=c.phone,
        email=c.email,
        loyalty_points=c.loyalty_points,
        created_at=c.created_at,
        updated_at=c.updated_at,
        total_sales_count=sales_count,
        total_spend=round(total_spend, 2)
    )


@router.get("", response_model=List[CustomerOut])
def list_customers(
    search: Optional[str] = Query(None, description="Search by customer name, phone, or email"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Retrieve customer profiles with optional name/phone/email search."""
    query = db.query(Customer)

    if search:
        search_fmt = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Customer.name.ilike(search_fmt),
                Customer.phone.ilike(search_fmt),
                Customer.email.ilike(search_fmt)
            )
        )

    customers = query.order_by(Customer.name.asc()).offset(skip).limit(limit).all()
    return [_to_customer_out(c, db) for c in customers]


@router.post("", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
def create_customer(customer_in: CustomerCreate, db: Session = Depends(get_db)):
    """Create a new customer profile."""
    # Check duplicate phone or email if provided
    if customer_in.phone:
        existing_phone = db.query(Customer).filter(Customer.phone == customer_in.phone.strip()).first()
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Customer with phone '{customer_in.phone}' already exists."
            )

    new_cust = Customer(
        name=customer_in.name.strip(),
        phone=customer_in.phone.strip() if customer_in.phone else None,
        email=customer_in.email.strip() if customer_in.email else None,
        loyalty_points=customer_in.loyalty_points or 0
    )
    db.add(new_cust)
    db.commit()
    db.refresh(new_cust)
    return _to_customer_out(new_cust, db)


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    """Retrieve customer details by ID."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return _to_customer_out(customer, db)


@router.put("/{customer_id}", response_model=CustomerOut)
def update_customer(customer_id: int, customer_in: CustomerUpdate, db: Session = Depends(get_db)):
    """Update customer profile information."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    update_data = customer_in.model_dump(exclude_unset=True)

    if "phone" in update_data and update_data["phone"]:
        dup_phone = db.query(Customer).filter(
            Customer.phone == update_data["phone"].strip(),
            Customer.id != customer_id
        ).first()
        if dup_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Another customer with phone '{update_data['phone']}' already exists."
            )

    for field, value in update_data.items():
        setattr(customer, field, value)

    db.commit()
    db.refresh(customer)
    return _to_customer_out(customer, db)


@router.delete("/{customer_id}", status_code=status.HTTP_200_OK)
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    """Delete a customer."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    db.delete(customer)
    db.commit()
    return {"message": f"Customer '{customer.name}' deleted successfully."}
