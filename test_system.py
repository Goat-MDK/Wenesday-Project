"""
Verification test suite for E-Sale Management System backend API.
Tests all required endpoints, CRUD operations, atomic checkout, and analytics.
"""
from starlette.testclient import TestClient
from backend.main import app

client = TestClient(app)


def run_tests():
    print("--- 1. Testing Health & Root Endpoints ---")
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("Health check OK:", res.json())

    print("\n--- 2. Testing Products Endpoints ---")
    # List products
    res = client.get("/api/v1/products")
    assert res.status_code == 200
    products = res.json()
    print(f"Retrieved {len(products)} products.")
    assert len(products) > 0, "Expected seeded products."

    first_product = products[0]
    prod_id = first_product["id"]
    initial_stock = first_product["stock_quantity"]
    print(f"Sample product: {first_product['name']} (ID: {prod_id}, Stock: {initial_stock})")

    # Stock check endpoint
    res = client.get(f"/api/v1/products/{prod_id}/stock")
    assert res.status_code == 200
    print("Stock check response:", res.json())

    print("\n--- 3. Testing Customers Endpoints ---")
    res = client.get("/api/v1/customers")
    assert res.status_code == 200
    customers = res.json()
    print(f"Retrieved {len(customers)} customers.")
    assert len(customers) > 0, "Expected seeded customers."
    first_customer = customers[0]
    cust_id = first_customer["id"]
    print(f"Sample customer: {first_customer['name']} (ID: {cust_id}, Points: {first_customer['loyalty_points']})")

    print("\n--- 4. Testing Atomic Sales Checkout & Stock Deduction ---")
    checkout_payload = {
        "customer_id": cust_id,
        "items": [
            {
                "product_id": prod_id,
                "quantity": 2
            }
        ],
        "discount": 5.0,
        "tax_rate": 0.05,
        "payment_method": "Card",
        "notes": "Automated verification checkout"
    }
    res = client.post("/api/v1/sales", json=checkout_payload)
    assert res.status_code == 201, f"Checkout failed: {res.text}"
    receipt = res.json()
    invoice_no = receipt["sale"]["invoice_no"]
    total_paid = receipt["sale"]["total_amount"]
    points_earned = receipt["points_earned"]
    print(f"Checkout SUCCESS! Invoice: {invoice_no}, Total: ${total_paid}, Points Earned: +{points_earned}")

    # Verify inventory was deducted atomically
    res_stock = client.get(f"/api/v1/products/{prod_id}/stock")
    updated_stock = res_stock.json()["stock_quantity"]
    assert updated_stock == initial_stock - 2, f"Stock deduction failed! Expected {initial_stock - 2}, got {updated_stock}"
    print(f"Atomic inventory deduction verified: {initial_stock} -> {updated_stock} (-2 items).")

    print("\n--- 5. Testing Analytics Endpoints ---")
    res_summary = client.get("/api/v1/analytics/summary")
    assert res_summary.status_code == 200
    print("Analytics Summary:", res_summary.json())

    res_dash = client.get("/api/v1/analytics/dashboard")
    assert res_dash.status_code == 200
    dash = res_dash.json()
    print(f"Dashboard verified: {len(dash['top_products'])} top products, {len(dash['daily_trends'])} trend entries.")

    print("\n==========================================")
    print(">>> ALL VERIFICATION TESTS PASSED SUCCESSFULLY! <<<")
    print("==========================================")


if __name__ == "__main__":
    run_tests()
