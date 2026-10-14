from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.database import get_db
from backend.models.product import Product
from backend.models.customer import Customer
from backend.models.sale import Sale, SaleItem
from backend.schemas.analytics import (
    AnalyticsSummary,
    TopProduct,
    SalesTrend,
    AnalyticsDashboardResponse
)

router = APIRouter(prefix="/analytics", tags=["Analytics & Dashboard"])


@router.get("/summary", response_model=AnalyticsSummary)
def get_analytics_summary(db: Session = Depends(get_db)):
    """Compute overall sales, revenue, cost, profit, and inventory alert metrics."""
    # Completed sales aggregation
    sales_stats = db.query(
        func.count(Sale.id),
        func.coalesce(func.sum(Sale.total_amount), 0.0)
    ).filter(Sale.status == "COMPLETED").first()

    total_sales_count = sales_stats[0] if sales_stats else 0
    total_revenue = float(sales_stats[1]) if sales_stats else 0.0

    # Total cost of goods sold (COGS)
    cogs_query = db.query(
        func.coalesce(func.sum(SaleItem.cost_price * SaleItem.quantity), 0.0)
    ).join(Sale, SaleItem.sale_id == Sale.id).filter(Sale.status == "COMPLETED").first()

    total_cost = float(cogs_query[0]) if cogs_query else 0.0
    total_profit = max(0.0, total_revenue - total_cost)
    profit_margin = round((total_profit / total_revenue * 100), 2) if total_revenue > 0 else 0.0
    aov = round((total_revenue / total_sales_count), 2) if total_sales_count > 0 else 0.0

    # Customer and Product counts
    customers_count = db.query(func.count(Customer.id)).scalar() or 0
    products_count = db.query(func.count(Product.id)).scalar() or 0
    low_stock_count = db.query(func.count(Product.id)).filter(
        Product.stock_quantity <= Product.low_stock_threshold,
        Product.is_active == True
    ).scalar() or 0

    return AnalyticsSummary(
        total_sales_count=total_sales_count,
        total_revenue=round(total_revenue, 2),
        total_cost=round(total_cost, 2),
        total_profit=round(total_profit, 2),
        profit_margin_percent=profit_margin,
        average_order_value=aov,
        total_customers_count=customers_count,
        total_products_count=products_count,
        low_stock_products_count=low_stock_count
    )


@router.get("/top-products", response_model=List[TopProduct])
def get_top_selling_products(
    limit: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Retrieve top-selling products by quantity sold and revenue."""
    results = db.query(
        Product.id,
        Product.sku,
        Product.name,
        Product.category,
        func.coalesce(func.sum(SaleItem.quantity), 0).label("total_qty"),
        func.coalesce(func.sum(SaleItem.subtotal), 0.0).label("total_rev"),
        func.coalesce(func.sum(SaleItem.subtotal - (SaleItem.cost_price * SaleItem.quantity)), 0.0).label("total_prof")
    ).join(SaleItem, Product.id == SaleItem.product_id)\
     .join(Sale, SaleItem.sale_id == Sale.id)\
     .filter(Sale.status == "COMPLETED")\
     .group_by(Product.id, Product.sku, Product.name, Product.category)\
     .order_by(desc("total_qty"))\
     .limit(limit)\
     .all()

    top_products = []
    for r in results:
        top_products.append(TopProduct(
            product_id=r[0],
            sku=r[1],
            name=r[2],
            category=r[3],
            total_quantity_sold=int(r[4]),
            total_revenue=round(float(r[5]), 2),
            total_profit=round(float(r[6]), 2)
        ))
    return top_products


@router.get("/trends", response_model=List[SalesTrend])
def get_sales_trends(
    days: int = Query(14, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """Retrieve daily sales revenue and profit for the past N days."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Query completed sales within date window
    sales = db.query(Sale).filter(
        Sale.status == "COMPLETED",
        Sale.created_at >= start_date
    ).all()

    # Aggregate by date string YYYY-MM-DD
    trend_map = {}
    for i in range(days + 1):
        day_str = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        trend_map[day_str] = {"count": 0, "revenue": 0.0, "profit": 0.0}

    for sale in sales:
        day_key = sale.created_at.strftime("%Y-%m-%d")
        if day_key in trend_map:
            trend_map[day_key]["count"] += 1
            rev = float(sale.total_amount)
            # Estimate cost from items
            cost = sum(float(it.cost_price) * it.quantity for it in sale.items)
            trend_map[day_key]["revenue"] += rev
            trend_map[day_key]["profit"] += max(0.0, rev - cost)

    trends = []
    for day_str in sorted(trend_map.keys()):
        data = trend_map[day_str]
        trends.append(SalesTrend(
            date=day_str,
            sales_count=data["count"],
            revenue=round(data["revenue"], 2),
            profit=round(data["profit"], 2)
        ))
    return trends


@router.get("/dashboard", response_model=AnalyticsDashboardResponse)
def get_full_dashboard(db: Session = Depends(get_db)):
    """Consolidated endpoint returning all KPI metrics, charts, and payment breakdowns."""
    summary = get_analytics_summary(db)
    top_products = get_top_selling_products(limit=5, db=db)
    daily_trends = get_sales_trends(days=14, db=db)

    # Payment method breakdown
    payment_counts = db.query(
        Sale.payment_method,
        func.count(Sale.id),
        func.sum(Sale.total_amount)
    ).filter(Sale.status == "COMPLETED").group_by(Sale.payment_method).all()

    payment_breakdown = {}
    for pm in payment_counts:
        payment_breakdown[pm[0]] = {
            "count": pm[1],
            "total": round(float(pm[2]), 2) if pm[2] else 0.0
        }

    return AnalyticsDashboardResponse(
        summary=summary,
        top_products=top_products,
        daily_trends=daily_trends,
        payment_method_breakdown=payment_breakdown
    )
