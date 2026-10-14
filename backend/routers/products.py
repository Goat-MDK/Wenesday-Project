from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from backend.database import get_db
from backend.models.product import Product
from backend.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductOut,
    StockCheckResponse,
    StockAdjustmentRequest
)

router = APIRouter(prefix="/products", tags=["Products"])


def _to_product_out(p: Product) -> ProductOut:
    return ProductOut(
        id=p.id,
        sku=p.sku,
        name=p.name,
        category=p.category,
        barcode=p.barcode,
        cost_price=float(p.cost_price),
        sale_price=float(p.sale_price),
        stock_quantity=p.stock_quantity,
        low_stock_threshold=p.low_stock_threshold,
        is_active=p.is_active,
        created_at=p.created_at,
        updated_at=p.updated_at,
        is_low_stock=(p.stock_quantity <= p.low_stock_threshold)
    )


@router.get("", response_model=List[ProductOut])
def list_products(
    search: Optional[str] = Query(None, description="Search by name, SKU, or barcode"),
    category: Optional[str] = Query(None, description="Filter by category"),
    low_stock_only: bool = Query(False, description="Filter only products with low stock"),
    active_only: bool = Query(True, description="Filter active products"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Retrieve all products with optional search, category, and low-stock filters."""
    query = db.query(Product)

    if active_only:
        query = query.filter(Product.is_active == True)

    if category and category.lower() != "all":
        query = query.filter(Product.category.ilike(category))

    if search:
        search_fmt = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_fmt),
                Product.sku.ilike(search_fmt),
                Product.barcode.ilike(search_fmt)
            )
        )

    if low_stock_only:
        query = query.filter(Product.stock_quantity <= Product.low_stock_threshold)

    products = query.order_by(Product.name.asc()).offset(skip).limit(limit).all()
    return [_to_product_out(p) for p in products]


@router.get("/categories", response_model=List[str])
def list_categories(db: Session = Depends(get_db)):
    """Retrieve unique product categories for UI filters."""
    categories = db.query(Product.category).distinct().filter(Product.category.isnot(None)).all()
    return sorted([c[0] for c in categories if c[0]])


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(product_in: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product with unique SKU and optional barcode check."""
    # Check duplicate SKU
    existing_sku = db.query(Product).filter(func.lower(Product.sku) == product_in.sku.lower()).first()
    if existing_sku:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with SKU '{product_in.sku}' already exists."
        )

    # Check duplicate Barcode if provided
    if product_in.barcode:
        existing_barcode = db.query(Product).filter(Product.barcode == product_in.barcode).first()
        if existing_barcode:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with barcode '{product_in.barcode}' already exists."
            )

    new_product = Product(
        sku=product_in.sku.strip(),
        name=product_in.name.strip(),
        category=product_in.category.strip(),
        barcode=product_in.barcode.strip() if product_in.barcode else None,
        cost_price=product_in.cost_price,
        sale_price=product_in.sale_price,
        stock_quantity=product_in.stock_quantity,
        low_stock_threshold=product_in.low_stock_threshold,
        is_active=product_in.is_active
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return _to_product_out(new_product)


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Retrieve a single product by its ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return _to_product_out(product)


@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, product_in: ProductUpdate, db: Session = Depends(get_db)):
    """Update product details."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    update_data = product_in.model_dump(exclude_unset=True)

    # Check SKU collision if changed
    if "sku" in update_data and update_data["sku"]:
        dup_sku = db.query(Product).filter(
            func.lower(Product.sku) == update_data["sku"].lower(),
            Product.id != product_id
        ).first()
        if dup_sku:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Another product with SKU '{update_data['sku']}' already exists."
            )

    # Check barcode collision if changed
    if "barcode" in update_data and update_data["barcode"]:
        dup_bc = db.query(Product).filter(
            Product.barcode == update_data["barcode"],
            Product.id != product_id
        ).first()
        if dup_bc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Another product with barcode '{update_data['barcode']}' already exists."
            )

    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return _to_product_out(product)


@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
def delete_product(product_id: int, hard_delete: bool = False, db: Session = Depends(get_db)):
    """Deactivate or permanently remove a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    if hard_delete:
        # Check if product is referenced in sale_items
        if product.sale_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot permanently delete product with existing sales history. Deactivate it instead."
            )
        db.delete(product)
        db.commit()
        return {"message": f"Product '{product.name}' was permanently deleted."}
    else:
        product.is_active = False
        db.commit()
        return {"message": f"Product '{product.name}' deactivated successfully."}


@router.get("/{product_id}/stock", response_model=StockCheckResponse)
def check_product_stock(product_id: int, db: Session = Depends(get_db)):
    """Check live stock status for POS registration or inventory audit."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    return StockCheckResponse(
        product_id=product.id,
        sku=product.sku,
        name=product.name,
        stock_quantity=product.stock_quantity,
        low_stock_threshold=product.low_stock_threshold,
        is_in_stock=(product.stock_quantity > 0),
        is_low_stock=(product.stock_quantity <= product.low_stock_threshold)
    )


@router.post("/{product_id}/adjust-stock", response_model=ProductOut)
def adjust_product_stock(
    product_id: int,
    adj: StockAdjustmentRequest,
    db: Session = Depends(get_db)
):
    """Adjust inventory up (restock) or down (waste/damage)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    new_stock = product.stock_quantity + adj.quantity_change
    if new_stock < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reduce stock below 0. Current stock: {product.stock_quantity}, adjustment: {adj.quantity_change}"
        )

    product.stock_quantity = new_stock
    db.commit()
    db.refresh(product)
    return _to_product_out(product)
