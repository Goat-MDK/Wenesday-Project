import random
from datetime import datetime, timedelta
from backend.database import SessionLocal, init_db
from backend.models.product import Product
from backend.models.customer import Customer
from backend.models.sale import Sale, SaleItem


def seed_database():
    """Populate database with realistic initial data for testing and demonstrations."""
    init_db()
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(Product).first():
            print("Database already contains data. Skipping seed.")
            return

        print("Seeding initial products...")
        sample_products = [
            # Electronics
            {"sku": "ELEC-1001", "name": "Logitech MX Master 3S Mouse", "category": "Electronics", "barcode": "097855174543", "cost_price": 65.00, "sale_price": 99.99, "stock_quantity": 25, "low_stock_threshold": 8},
            {"sku": "ELEC-1002", "name": "Keychron K2 Mechanical Keyboard", "category": "Electronics", "barcode": "097855174550", "cost_price": 55.00, "sale_price": 89.00, "stock_quantity": 18, "low_stock_threshold": 5},
            {"sku": "ELEC-1003", "name": "Sony WH-1000XM5 Headphones", "category": "Electronics", "barcode": "027242923126", "cost_price": 240.00, "sale_price": 349.99, "stock_quantity": 6, "low_stock_threshold": 5},
            {"sku": "ELEC-1004", "name": "Anker 65W GaN Fast Charger", "category": "Electronics", "barcode": "194644049874", "cost_price": 18.00, "sale_price": 35.99, "stock_quantity": 4, "low_stock_threshold": 10},  # Low stock alert!
            {"sku": "ELEC-1005", "name": "Dell UltraSharp 27\" 4K Monitor", "category": "Electronics", "barcode": "884116382103", "cost_price": 380.00, "sale_price": 549.00, "stock_quantity": 3, "low_stock_threshold": 4},  # Low stock alert!
            
            # Accessories
            {"sku": "ACC-2001", "name": "Aluminum Laptop Stand", "category": "Accessories", "barcode": "692181561011", "cost_price": 12.50, "sale_price": 29.99, "stock_quantity": 40, "low_stock_threshold": 10},
            {"sku": "ACC-2002", "name": "Braided USB-C to USB-C Cable (2m)", "category": "Accessories", "barcode": "692181561028", "cost_price": 3.00, "sale_price": 12.99, "stock_quantity": 75, "low_stock_threshold": 15},
            {"sku": "ACC-2003", "name": "Ergonomic Memory Foam Wrist Rest", "category": "Accessories", "barcode": "692181561035", "cost_price": 6.00, "sale_price": 16.50, "stock_quantity": 2, "low_stock_threshold": 10},  # Low stock alert!
            {"sku": "ACC-2004", "name": "Water-Resistant Laptop Sleeve 14\"", "category": "Accessories", "barcode": "692181561042", "cost_price": 9.00, "sale_price": 22.00, "stock_quantity": 20, "low_stock_threshold": 5},

            # Office Supplies
            {"sku": "OFF-3001", "name": "Moleskine Hardcover Ruled Notebook", "category": "Office", "barcode": "9788883701122", "cost_price": 9.50, "sale_price": 19.95, "stock_quantity": 30, "low_stock_threshold": 10},
            {"sku": "OFF-3002", "name": "Lamy Safari Fountain Pen - Charcoal", "category": "Office", "barcode": "4014519018420", "cost_price": 15.00, "sale_price": 29.50, "stock_quantity": 14, "low_stock_threshold": 5},
            {"sku": "OFF-3003", "name": "Sticky Notes Neon Pack (6 Pads)", "category": "Office", "barcode": "051131001234", "cost_price": 2.50, "sale_price": 7.99, "stock_quantity": 50, "low_stock_threshold": 15},
        ]

        created_products = []
        for p in sample_products:
            prod = Product(**p)
            db.add(prod)
            created_products.append(prod)
        db.commit()

        print("Seeding initial customers...")
        sample_customers = [
            {"name": "Alice Johnson", "phone": "+1-555-0101", "email": "alice.j@example.com", "loyalty_points": 45},
            {"name": "Bob Martinez", "phone": "+1-555-0102", "email": "bob.m@example.com", "loyalty_points": 120},
            {"name": "Charlie Davis", "phone": "+1-555-0103", "email": "charlie.d@example.com", "loyalty_points": 80},
            {"name": "Diana Prince", "phone": "+1-555-0104", "email": "diana.p@example.com", "loyalty_points": 15},
            {"name": "Ethan Hunt", "phone": "+1-555-0105", "email": "ethan.h@example.com", "loyalty_points": 210},
        ]

        created_customers = []
        for c in sample_customers:
            cust = Customer(**c)
            db.add(cust)
            created_customers.append(cust)
        db.commit()

        print("Seeding historical sales transactions...")
        payment_methods = ["Cash", "Card", "Digital Transfer"]
        now = datetime.now()

        for i in range(18):
            sale_date = now - timedelta(days=random.randint(0, 12), hours=random.randint(1, 10))
            cust = random.choice(created_customers + [None, None])  # Some walk-ins
            pm = random.choice(payment_methods)

            # Random 1-3 items
            selected_prods = random.sample(created_products, k=random.randint(1, 3))
            subtotal = 0.0
            items_to_add = []

            for p in selected_prods:
                qty = random.randint(1, 2)
                unit_p = float(p.sale_price)
                cost_p = float(p.cost_price)
                line_sub = round(unit_p * qty, 2)
                subtotal += line_sub

                items_to_add.append(
                    SaleItem(
                        product_id=p.id,
                        quantity=qty,
                        unit_price=unit_p,
                        cost_price=cost_p,
                        subtotal=line_sub
                    )
                )

            discount = 5.00 if subtotal > 100 and random.random() > 0.5 else 0.00
            taxable = max(0.0, subtotal - discount)
            tax = round(taxable * 0.05, 2)
            total = round(taxable + tax, 2)

            invoice_code = f"INV-{sale_date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            sale = Sale(
                invoice_no=invoice_code,
                customer_id=cust.id if cust else None,
                subtotal=subtotal,
                discount=discount,
                tax=tax,
                total_amount=total,
                payment_method=pm,
                status="COMPLETED",
                created_at=sale_date
            )
            db.add(sale)
            db.flush()

            for itm in items_to_add:
                itm.sale_id = sale.id
                db.add(itm)

        db.commit()
        print("Successfully seeded database with products, customers, and sales!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
