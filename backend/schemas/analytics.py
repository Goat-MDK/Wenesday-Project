from typing import List, Optional
from pydantic import BaseModel


class AnalyticsSummary(BaseModel):
    total_sales_count: int
    total_revenue: float
    total_cost: float
    total_profit: float
    profit_margin_percent: float
    average_order_value: float
    total_customers_count: int
    total_products_count: int
    low_stock_products_count: int


class TopProduct(BaseModel):
    product_id: int
    sku: str
    name: str
    category: str
    total_quantity_sold: int
    total_revenue: float
    total_profit: float


class SalesTrend(BaseModel):
    date: str
    sales_count: int
    revenue: float
    profit: float


class AnalyticsDashboardResponse(BaseModel):
    summary: AnalyticsSummary
    top_products: List[TopProduct]
    daily_trends: List[SalesTrend]
    payment_method_breakdown: dict
