import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from backend.database import get_db
from backend.models.product import Product
from backend.models.customer import Customer
from backend.models.sale import Sale, SaleItem
from backend.schemas.sale import (
    CheckoutRequest,
    SaleOut,
    SaleItemOut,
    SaleReceipt
)

router = APIRouter(prefix="/sales", tags=["Sales & POS Checkout"])


def _generate_invoice_no(db: Session) -> str:
    """Generate a clean, unique invoice number: INV-YYYYMMDD-XXXX."""
    date_str = datetime.now().strftime("%Y%m%d")
    unique_suffix = uuid.uuid4().hex[:6].upper()
    return f"INV-{date_str}-{unique_suffix}"


def _to_sale_out(s: Sale) -> SaleOut:
    items_out = []
    for item in s.items:
        items_out.append(SaleItemOut(
            id=item.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=float(item.unit_price),
            cost_price=float(item.cost_price),
            subtotal=float(item.subtotal),
            product_name=item.product.name if item.product else f"Product #{item.product_id}",
            product_sku=item.product.sku if item.product else "N/A"
        ))

    return SaleOut(
        id=s.id,
        invoice_no=s.invoice_no,
        customer_id=s.customer_id,
        customer_name=s.customer.name if s.customer else "Walk-in Customer",
        subtotal=round(float(s.subtotal), 2),
        discount=round(float(s.discount), 2),
        tax=round(float(s.tax), 2),
        total_amount=round(float(s.total_amount), 2),
        payment_method=s.payment_method,
        status=s.status,
        notes=s.notes,
        created_at=s.created_at,
        items=items_out
    )


@router.post("", response_model=SaleReceipt, status_code=status.HTTP_201_CREATED)
def checkout_sale(order: CheckoutRequest, db: Session = Depends(get_db)):
    """
    POS Atomic Checkout:
    1. Validates all requested products and verifies stock levels.
    2. Atomically decrements product stock quantities.
    3. Calculates subtotal, discount, tax, and final total.
    4. Records customer loyalty points if a registered customer is provided.
    5. Saves Sale and SaleItem records in a single transactional unit.
    """
    if not order.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot complete checkout: Cart is empty."
        )

    # 1. Verify Customer if provided
    customer = None
    if order.customer_id:
        customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer ID {order.customer_id} does not exist."
            )

    # Begin atomic transaction block
    try:
        calculated_subtotal = 0.0
        sale_items_to_create = []

        # 2. Validate products and inventory
        for item_req in order.items:
            # Query product with row lock if postgres
            product = db.query(Product).filter(Product.id == item_req.product_id).with_for_update().first()
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with ID {item_req.product_id} not found."
                )

            if not product.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product '{product.name}' (SKU: {product.sku}) is currently deactivated."
                )

            if product.stock_quantity < item_req.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient inventory for '{product.name}'. Available: {product.stock_quantity}, Requested: {item_req.quantity}"
                )

            # Deduct stock in real time
            product.stock_quantity -= item_req.quantity

            # Determine unit price (override or product sale_price)
            unit_price = item_req.unit_price if item_req.unit_price is not None else float(product.sale_price)
            cost_price = float(product.cost_price)
            item_subtotal = round(unit_price * item_req.quantity, 2)
            calculated_subtotal += item_subtotal

            # Prepare sale item model
            sale_item = SaleItem(
                product_id=product.id,
                quantity=item_req.quantity,
                unit_price=unit_price,
                cost_price=cost_price,
                subtotal=item_subtotal
            )
            sale_items_to_create.append(sale_item)

        # 3. Compute final totals
        calculated_subtotal = round(calculated_subtotal, 2)
        discount = round(min(order.discount, calculated_subtotal), 2)
        taxable_amount = calculated_subtotal - discount
        tax = round(taxable_amount * order.tax_rate, 2)
        total_amount = round(taxable_amount + tax, 2)

        # 4. Generate invoice
        invoice_no = _generate_invoice_no(db)

        # 5. Create Sale
        new_sale = Sale(
            invoice_no=invoice_no,
            customer_id=customer.id if customer else None,
            subtotal=calculated_subtotal,
            discount=discount,
            tax=tax,
            total_amount=total_amount,
            payment_method=order.payment_method,
            status="COMPLETED",
            notes=order.notes
        )
        db.add(new_sale)
        db.flush()  # Populates new_sale.id

        # Associate items with sale
        for item in sale_items_to_create:
            item.sale_id = new_sale.id
            db.add(item)

        # 6. Award loyalty points (1 point per 10 currency units spent)
        points_earned = 0
        if customer:
            points_earned = int(total_amount // 10)
            customer.loyalty_points += points_earned

        db.commit()
        db.refresh(new_sale)

        return SaleReceipt(
            sale=_to_sale_out(new_sale),
            items_count=len(new_sale.items),
            points_earned=points_earned
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing checkout: {str(e)}"
        )


@router.get("", response_model=List[SaleOut])
def list_sales(
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    payment_method: Optional[str] = Query(None, description="Filter by payment method"),
    status_filter: Optional[str] = Query(None, description="Filter by status (COMPLETED, REFUNDED)"),
    search: Optional[str] = Query(None, description="Search by invoice number"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Retrieve historical sales transactions with optional filters."""
    query = db.query(Sale)

    if customer_id:
        query = query.filter(Sale.customer_id == customer_id)

    if payment_method and payment_method.lower() != "all":
        query = query.filter(Sale.payment_method.ilike(payment_method))

    if status_filter and status_filter.lower() != "all":
        query = query.filter(Sale.status.ilike(status_filter))

    if search:
        query = query.filter(Sale.invoice_no.ilike(f"%{search.strip()}%"))

    sales = query.order_by(desc(Sale.created_at)).offset(skip).limit(limit).all()
    return [_to_sale_out(s) for s in sales]


@router.get("/{identifier}", response_model=SaleOut)
def get_sale_details(identifier: str, db: Session = Depends(get_db)):
    """Retrieve full sale details by database ID or Invoice number."""
    if identifier.isdigit():
        sale = db.query(Sale).filter(Sale.id == int(identifier)).first()
    else:
        sale = db.query(Sale).filter(Sale.invoice_no.ilike(identifier.strip())).first()

    if not sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale transaction not found")

    return _to_sale_out(sale)


@router.post("/{sale_id}/refund", response_model=SaleOut)
def refund_sale(sale_id: int, reason: Optional[str] = None, db: Session = Depends(get_db)):
    """Refund a completed transaction and restore inventory."""
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")

    if sale.status == "REFUNDED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sale is already refunded.")

    try:
        # Restore stock for each item
        for item in sale.items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                product.stock_quantity += item.quantity

        sale.status = "REFUNDED"
        if reason:
            sale.notes = f"{sale.notes or ''} [REFUND REASON: {reason}]"

        db.commit()
        db.refresh(sale)
        return _to_sale_out(sale)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Refund failed: {str(e)}"
        )
