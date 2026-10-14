import os
from typing import Any, Dict, List, Optional, Tuple
import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v1").rstrip("/")


class APIClient:
    """REST API Client for communicating with the FastAPI backend."""

    def __init__(self, base_url: str = API_BASE_URL, timeout: int = 10):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()

    def _url(self, endpoint: str) -> str:
        return f"{self.base_url}{endpoint if endpoint.startswith('/') else '/' + endpoint}"

    def _handle_response(self, response: requests.Response) -> Tuple[bool, Any]:
        try:
            data = response.json()
        except Exception:
            data = response.text

        if 200 <= response.status_code < 300:
            return True, data
        else:
            error_msg = data.get("detail", str(data)) if isinstance(data, dict) else str(data)
            return False, error_msg

    # --- System / Health ---
    def check_health(self) -> Tuple[bool, Any]:
        try:
            root_url = self.base_url.replace("/api/v1", "/health")
            res = self.session.get(root_url, timeout=3)
            return self._handle_response(res)
        except requests.exceptions.RequestException as e:
            return False, f"Could not reach backend at {self.base_url}. Is FastAPI running? ({str(e)})"

    # --- Products ---
    def get_products(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        low_stock_only: bool = False,
        active_only: bool = True
    ) -> Tuple[bool, Any]:
        params = {
            "low_stock_only": low_stock_only,
            "active_only": active_only,
            "limit": 200
        }
        if search:
            params["search"] = search
        if category and category != "All":
            params["category"] = category

        try:
            res = self.session.get(self._url("/products"), params=params, timeout=self.timeout)
            return self._handle_response(res)
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"

    def get_categories(self) -> Tuple[bool, Any]:
        try:
            res = self.session.get(self._url("/products/categories"), timeout=self.timeout)
            return self._handle_response(res)
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"

    def create_product(self, product_data: Dict[str, Any]) -> Tuple[bool, Any]:
        try:
            res = self.session.post(self._url("/products"), json=product_data, timeout=self.timeout)
            return self._handle_response(res)
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"

    def update_product(self, product_id: int, product_data: Dict[str, Any]) -> Tuple[bool, Any]:
        try:
            res = self.session.put(self._url(f"/products/{product_id}"), json=product_data, timeout=self.timeout)
            return self._handle_response(res)
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"

    def delete_product(self, product_id: int, hard_delete: bool = False) -> Tuple[bool, Any]:
        try:
            res = self.session.delete(
                self._url(f"/products/{product_id}"),
                params={"hard_delete": hard_delete},
                timeout=self.timeout
            )
            return self._handle_response(res)
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"

    def adjust_stock(self, product_id: int, quantity_change: int, reason: str = "Manual adjustment") -> Tuple[bool, Any]:
        try:
            res = self.session.post(
                self._url(f"/products/{product_id}/adjust-stock"),
                json={"quantity_change": quantity_change, "reason": reason},
                timeout=self.timeout
            )
            return self._handle_response(res)
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"

    # --- Customers ---
    def get_customers(self, search: Optional[str] = None) -> Tuple[bool, Any]:
        params = {"limit": 200}
        if search:
            params["search"] = search
        try:
            res = self.session.get(self._url("/customers"), params=params, timeout=self.timeout)
            return self._handle_response(res)
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"

    def create_customer(self, customer_data: Dict[str, Any]) -> Tuple[bool, Any]:
        try:
            res = self.session.post(self._url("/customers"), json=customer_data, timeout=self.timeout)
            return self._handle_response(res)
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"

    def update_customer(self, customer_id: int, customer_data: Dict[str, Any]) -> Tuple[bool, Any]:
        try:
            res = self.session.put(self._url(f"/customers/{customer_id}"), json=customer_data, timeout=self.timeout)
            return self._handle_response(res)
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"

    def delete_customer(self, customer_id: int) -> Tuple[bool, Any]:
        try:
            res = self.session.delete(self._url(f"/customers/{customer_id}"), timeout=self.timeout)
            return self._handle_response(res)
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"

    # --- Sales & POS Checkout ---
    def checkout_sale(self, payload: Dict[str, Any]) -> Tuple[bool, Any]:
        try:
            res = self.session.post(self._url("/sales"), json=payload, timeout=self.timeout)
            return self._handle_response(res)
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"

    def get_sales(
        self,
        search: Optional[str] = None,
        payment_method: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 50
    ) -> Tuple[bool, Any]:
        params = {"limit": limit}
        if search:
            params["search"] = search
        if payment_method and payment_method != "All":
            params["payment_method"] = payment_method
        if status_filter and status_filter != "All":
            params["status_filter"] = status_filter

        try:
            res = self.session.get(self._url("/sales"), params=params, timeout=self.timeout)
            return self._handle_response(res)
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"

    def get_sale(self, identifier: str) -> Tuple[bool, Any]:
        try:
            res = self.session.get(self._url(f"/sales/{identifier}"), timeout=self.timeout)
            return self._handle_response(res)
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"

    def refund_sale(self, sale_id: int, reason: str = "Customer Request") -> Tuple[bool, Any]:
        try:
            res = self.session.post(
                self._url(f"/sales/{sale_id}/refund"),
                params={"reason": reason},
                timeout=self.timeout
            )
            return self._handle_response(res)
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"

    # --- Analytics & Dashboard ---
    def get_full_dashboard(self) -> Tuple[bool, Any]:
        try:
            res = self.session.get(self._url("/analytics/dashboard"), timeout=self.timeout)
            return self._handle_response(res)
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"


# Singleton client instance
api = APIClient()
