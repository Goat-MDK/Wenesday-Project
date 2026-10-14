from backend.routers.products import router as products_router
from backend.routers.customers import router as customers_router
from backend.routers.sales import router as sales_router
from backend.routers.analytics import router as analytics_router

__all__ = ["products_router", "customers_router", "sales_router", "analytics_router"]
