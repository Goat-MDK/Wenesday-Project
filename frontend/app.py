import streamlit as st
import pandas as pd
from datetime import datetime
from frontend.api_client import api

# Configure Streamlit page
st.set_page_config(
    page_title="E-Sale POS & Management System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern, polished UI
st.markdown("""
<style>
    /* Metric Cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 16px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    
    /* POS Product Card */
    .pos-card {
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 12px;
        background-color: rgba(255, 255, 255, 0.02);
        transition: transform 0.15s ease-in-out, border-color 0.15s ease-in-out;
    }
    .pos-card:hover {
        border-color: #3b82f6;
        transform: translateY(-2px);
    }
    
    /* Stock Badges */
    .badge-instock {
        background-color: #10b981;
        color: white;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
    }
    .badge-lowstock {
        background-color: #f59e0b;
        color: white;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
    }
    .badge-outstock {
        background-color: #ef4444;
        color: white;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
    }
    
    /* Receipt Box */
    .receipt-container {
        font-family: 'Courier New', Courier, monospace;
        background: #f8fafc;
        color: #1e293b;
        border: 2px dashed #94a3b8;
        padding: 20px;
        border-radius: 8px;
        margin: 15px 0;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Session State
if "cart" not in st.session_state:
    st.session_state.cart = {}  # {product_id: {"name": str, "sku": str, "sale_price": float, "qty": int, "stock": int}}
if "last_receipt" not in st.session_state:
    st.session_state.last_receipt = None


# --- SIDEBAR NAVIGATION ---
st.sidebar.title("⚡ E-Sale Manager")
st.sidebar.caption("Full-Stack POS & Inventory Platform")

# Backend Health Check
healthy, health_data = api.check_health()
if healthy:
    st.sidebar.success("🟢 Backend Connected (FastAPI)")
else:
    st.sidebar.error("🔴 Backend Offline")
    st.sidebar.info("Run in terminal:\n`uvicorn backend.main:app --reload`")

nav_choice = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard & Analytics", "🛒 POS Sales Register", "📦 Inventory Management", "👥 Customer Profiles"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔗 Quick Links")
st.sidebar.markdown("[📘 Swagger API Docs](http://127.0.0.1:8000/docs)")
st.sidebar.markdown("[📗 ReDoc Specification](http://127.0.0.1:8000/redoc)")


# =========================================================================
# 1. DASHBOARD & ANALYTICS
# =========================================================================
if nav_choice == "📊 Dashboard & Analytics":
    st.title("📊 Executive Dashboard & Analytics")
    st.write("Real-time revenue, gross profit, sales trends, and inventory health.")

    success, dash_data = api.get_full_dashboard()

    if not success:
        st.error(f"Failed to load analytics: {dash_data}")
    else:
        summary = dash_data["summary"]
        top_prods = dash_data["top_products"]
        trends = dash_data["daily_trends"]
        payment_methods = dash_data["payment_method_breakdown"]

        # KPI Metric Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("💰 Total Revenue", f"${summary['total_revenue']:,.2f}", f"{summary['total_sales_count']} sales")
        m2.metric("📈 Gross Profit", f"${summary['total_profit']:,.2f}", f"{summary['profit_margin_percent']}% margin")
        m3.metric("🧾 Average Order Value", f"${summary['average_order_value']:,.2f}")
        m4.metric("⚠️ Low Stock Alerts", f"{summary['low_stock_products_count']} items", delta_color="inverse")

        st.markdown("---")

        # Charts Section
        c1, c2 = st.columns([2, 1])

        with c1:
            st.subheader("📈 14-Day Revenue & Profit Trends")
            if trends:
                df_trends = pd.DataFrame(trends)
                df_trends["date"] = pd.to_datetime(df_trends["date"])
                df_trends = df_trends.set_index("date")
                st.line_chart(df_trends[["revenue", "profit"]], use_container_width=True)
            else:
                st.info("No transaction data available yet.")

        with c2:
            st.subheader("💳 Payment Methods")
            if payment_methods:
                pm_data = []
                for pm_name, info in payment_methods.items():
                    pm_data.append({"Method": pm_name, "Orders": info["count"], "Volume ($)": info["total"]})
                st.dataframe(pd.DataFrame(pm_data), hide_index=True, use_container_width=True)
            else:
                st.info("No payments recorded.")

        st.markdown("---")

        # Top Selling Products & Recent Transactions
        col_top, col_recent = st.columns(2)

        with col_top:
            st.subheader("🏆 Top-Selling Products")
            if top_prods:
                df_top = pd.DataFrame(top_prods)
                df_top = df_top[["name", "category", "total_quantity_sold", "total_revenue", "total_profit"]]
                df_top.columns = ["Product", "Category", "Qty Sold", "Revenue ($)", "Profit ($)"]
                st.dataframe(df_top, hide_index=True, use_container_width=True)
            else:
                st.info("No sales yet to rank top products.")

        with col_recent:
            st.subheader("🧾 Recent Sales Transactions")
            s_ok, sales_data = api.get_sales(limit=10)
            if s_ok and sales_data:
                df_sales = pd.DataFrame(sales_data)
                df_sales["Date"] = pd.to_datetime(df_sales["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
                display_sales = df_sales[["invoice_no", "customer_name", "total_amount", "payment_method", "status", "Date"]]
                display_sales.columns = ["Invoice #", "Customer", "Total ($)", "Payment", "Status", "Date"]
                st.dataframe(display_sales, hide_index=True, use_container_width=True)
            else:
                st.info("No recent sales records.")


# =========================================================================
# 2. POS SALES REGISTER
# =========================================================================
elif nav_choice == "🛒 POS Sales Register":
    st.title("🛒 POS Checkout & Cashier Register")

    col_products, col_cart = st.columns([3, 2])

    # Left Column: Product Selection & Catalog
    with col_products:
        st.subheader("📦 Product Catalog")

        # Search and Category filter
        s_col1, s_col2 = st.columns([2, 1])
        with s_col1:
            search_query = st.text_input("🔍 Search Product (Name, SKU, Barcode)", placeholder="Type or scan barcode...")
        with s_col2:
            ok_cats, cat_list = api.get_categories()
            categories = ["All"] + (cat_list if ok_cats else [])
            selected_cat = st.selectbox("Category", categories)

        # Fetch products from API
        p_ok, products = api.get_products(
            search=search_query if search_query else None,
            category=selected_cat if selected_cat != "All" else None
        )

        if p_ok and products:
            # Display items in responsive columns
            num_cols = 2
            prod_cols = st.columns(num_cols)

            for idx, p in enumerate(products):
                col = prod_cols[idx % num_cols]
                with col:
                    stock_qty = p["stock_quantity"]
                    threshold = p["low_stock_threshold"]

                    if stock_qty <= 0:
                        stock_badge = '<span class="badge-outstock">OUT OF STOCK</span>'
                        can_add = False
                    elif stock_qty <= threshold:
                        stock_badge = f'<span class="badge-lowstock">LOW STOCK ({stock_qty})</span>'
                        can_add = True
                    else:
                        stock_badge = f'<span class="badge-instock">IN STOCK ({stock_qty})</span>'
                        can_add = True

                    st.markdown(f"""
                    <div class="pos-card">
                        <strong>{p['name']}</strong><br/>
                        <small style="color: gray;">SKU: {p['sku']} | {p['category']}</small><br/>
                        <div style="margin-top: 6px; display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 16px; font-weight: 700; color: #3b82f6;">${p['sale_price']:.2f}</span>
                            {stock_badge}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    btn_col1, btn_col2 = st.columns([3, 1])
                    with btn_col1:
                        if st.button(f"➕ Add to Cart", key=f"add_{p['id']}", disabled=not can_add):
                            p_id = p["id"]
                            if p_id in st.session_state.cart:
                                if st.session_state.cart[p_id]["qty"] < stock_qty:
                                    st.session_state.cart[p_id]["qty"] += 1
                                else:
                                    st.toast(f"Cannot exceed available stock of {stock_qty} for {p['name']}", icon="⚠️")
                            else:
                                st.session_state.cart[p_id] = {
                                    "name": p["name"],
                                    "sku": p["sku"],
                                    "sale_price": p["sale_price"],
                                    "qty": 1,
                                    "stock": stock_qty
                                }
                            st.rerun()
        else:
            st.info("No matching products found.")

    # Right Column: Cart & Checkout
    with col_cart:
        st.subheader("🛍️ Shopping Cart")

        if not st.session_state.cart:
            st.write("Your cart is empty. Add products from the catalog.")
        else:
            cart_subtotal = 0.0

            # Render Cart Items
            for p_id, item in list(st.session_state.cart.items()):
                item_sub = item["sale_price"] * item["qty"]
                cart_subtotal += item_sub

                c_info, c_dec, c_qty, c_inc, c_del = st.columns([3, 1, 1, 1, 1])
                with c_info:
                    st.write(f"**{item['name']}**")
                    st.caption(f"${item['sale_price']:.2f} each")
                with c_dec:
                    if st.button("➖", key=f"dec_{p_id}"):
                        if item["qty"] > 1:
                            st.session_state.cart[p_id]["qty"] -= 1
                        else:
                            del st.session_state.cart[p_id]
                        st.rerun()
                with c_qty:
                    st.write(f"**{item['qty']}**")
                with c_inc:
                    if st.button("➕", key=f"inc_{p_id}"):
                        if item["qty"] < item["stock"]:
                            st.session_state.cart[p_id]["qty"] += 1
                        else:
                            st.toast(f"Max stock reached ({item['stock']})", icon="⚠️")
                        st.rerun()
                with c_del:
                    if st.button("🗑️", key=f"del_{p_id}"):
                        del st.session_state.cart[p_id]
                        st.rerun()

            st.markdown("---")

            # Customer Selection
            c_ok, customers = api.get_customers()
            cust_options = {"None (Walk-in Customer)": None}
            if c_ok and customers:
                for cust in customers:
                    label = f"{cust['name']} ({cust.get('phone') or cust.get('email') or 'No contact'}) - {cust['loyalty_points']} pts"
                    cust_options[label] = cust["id"]

            selected_cust_label = st.selectbox("Customer", list(cust_options.keys()))
            chosen_customer_id = cust_options[selected_cust_label]

            # Financial Adjustments
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                discount_val = st.number_input("Discount ($)", min_value=0.0, max_value=float(cart_subtotal), value=0.0, step=1.0)
            with f_col2:
                tax_rate_pct = st.selectbox("Tax Rate", [("5% (Standard)", 0.05), ("0% (Tax Exempt)", 0.00), ("10% (Luxury)", 0.10)], index=0)
                tax_rate = tax_rate_pct[1]

            # Payment Method
            payment_choice = st.selectbox("Payment Method", ["Cash", "Card", "Digital Transfer"])
            sale_notes = st.text_input("Receipt Notes", placeholder="e.g. Counter #2, Gift wrap")

            # Totals Calculation
            taxable = max(0.0, cart_subtotal - discount_val)
            tax_amount = taxable * tax_rate
            total_bill = taxable + tax_amount

            st.markdown(f"""
            <div style="background: rgba(59, 130, 246, 0.08); padding: 14px 18px; border-radius: 8px; border: 1px solid rgba(59, 130, 246, 0.2);">
                <div style="display: flex; justify-content: space-between;"><span>Subtotal:</span><span>${cart_subtotal:.2f}</span></div>
                <div style="display: flex; justify-content: space-between; color: #f59e0b;"><span>Discount:</span><span>-${discount_val:.2f}</span></div>
                <div style="display: flex; justify-content: space-between;"><span>Tax ({int(tax_rate*100)}%):</span><span>${tax_amount:.2f}</span></div>
                <hr style="margin: 8px 0;"/>
                <div style="display: flex; justify-content: space-between; font-size: 19px; font-weight: 800; color: #10b981;">
                    <span>Total Amount:</span><span>${total_bill:.2f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.write("")
            btn_checkout_col1, btn_checkout_col2 = st.columns([2, 1])

            with btn_checkout_col1:
                if st.button("🚀 Complete Checkout", type="primary", use_container_width=True):
                    # Construct checkout payload
                    checkout_items = [
                        {"product_id": pid, "quantity": item["qty"], "unit_price": item["sale_price"]}
                        for pid, item in st.session_state.cart.items()
                    ]

                    payload = {
                        "customer_id": chosen_customer_id,
                        "items": checkout_items,
                        "discount": discount_val,
                        "tax_rate": tax_rate,
                        "payment_method": payment_choice,
                        "notes": sale_notes if sale_notes else None
                    }

                    with st.spinner("Processing transaction atomically..."):
                        ch_ok, receipt_res = api.checkout_sale(payload)

                    if ch_ok:
                        st.session_state.last_receipt = receipt_res
                        st.session_state.cart = {}
                        st.success(f"Sale Completed! Invoice: {receipt_res['sale']['invoice_no']}")
                        st.rerun()
                    else:
                        st.error(f"Checkout Failed: {receipt_res}")

            with btn_checkout_col2:
                if st.button("Clear Cart", use_container_width=True):
                    st.session_state.cart = {}
                    st.rerun()

        # Display Receipt Modal / Container if available
        if st.session_state.last_receipt:
            receipt = st.session_state.last_receipt
            sale_obj = receipt["sale"]

            st.markdown("### 🧾 Official Sales Receipt")
            receipt_html = f"""
            <div class="receipt-container">
                <center>
                    <h3 style="margin:0;">⚡ E-SALE STORE</h3>
                    <p style="margin:0;">Official Sales Invoice</p>
                    <small>Invoice: {sale_obj['invoice_no']} | Date: {sale_obj['created_at'][:19]}</small>
                </center>
                <hr style="border: 0.5px dashed #94a3b8;"/>
                <p><strong>Customer:</strong> {sale_obj['customer_name']}<br/>
                <strong>Payment:</strong> {sale_obj['payment_method']} | <strong>Status:</strong> {sale_obj['status']}</p>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="border-bottom: 1px solid #94a3b8; text-align: left;">
                            <th>Item</th><th>Qty</th><th>Price</th><th>Subtotal</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            for itm in sale_obj["items"]:
                receipt_html += f"""
                    <tr>
                        <td>{itm['product_name']}</td>
                        <td>{itm['quantity']}</td>
                        <td>${itm['unit_price']:.2f}</td>
                        <td>${itm['subtotal']:.2f}</td>
                    </tr>
                """
            receipt_html += f"""
                    </tbody>
                </table>
                <hr style="border: 0.5px dashed #94a3b8;"/>
                <div style="text-align: right;">
                    <p style="margin: 2px;">Subtotal: ${sale_obj['subtotal']:.2f}</p>
                    <p style="margin: 2px;">Discount: -${sale_obj['discount']:.2f}</p>
                    <p style="margin: 2px;">Tax: ${sale_obj['tax']:.2f}</p>
                    <h3 style="margin: 4px 0; color: #047857;">TOTAL PAID: ${sale_obj['total_amount']:.2f}</h3>
                    <small style="color: #64748b;">Loyalty Points Earned: +{receipt.get('points_earned', 0)} pts</small>
                </div>
                <center style="margin-top: 15px;"><small>*** THANK YOU FOR SHOPPING WITH US! ***</small></center>
            </div>
            """
            st.markdown(receipt_html, unsafe_allow_html=True)
            if st.button("Close Receipt"):
                st.session_state.last_receipt = None
                st.rerun()


# =========================================================================
# 3. INVENTORY MANAGEMENT
# =========================================================================
elif nav_choice == "📦 Inventory Management":
    st.title("📦 Product Inventory Management")

    tab_list, tab_add, tab_adjust = st.tabs(["📋 Products Directory", "➕ Add New Product", "⚖️ Stock Adjustment"])

    # TAB 1: Product List & Live Table
    with tab_list:
        f1, f2, f3 = st.columns([2, 1, 1])
        with f1:
            inv_search = st.text_input("Search Inventory (SKU, Name, Barcode)", key="inv_search")
        with f2:
            ok_cats, cat_list = api.get_categories()
            inv_cat = st.selectbox("Category Filter", ["All"] + (cat_list if ok_cats else []), key="inv_cat")
        with f3:
            low_stock_filter = st.checkbox("⚠️ Low Stock Only", value=False)

        ok_prod, prods = api.get_products(
            search=inv_search if inv_search else None,
            category=inv_cat if inv_cat != "All" else None,
            low_stock_only=low_stock_filter,
            active_only=False
        )

        if ok_prod and prods:
            df = pd.DataFrame(prods)
            # Add computed status column
            def stock_status(row):
                if not row["is_active"]:
                    return "Deactivated"
                if row["stock_quantity"] <= 0:
                    return "Out of Stock"
                if row["stock_quantity"] <= row["low_stock_threshold"]:
                    return "Low Stock Alert"
                return "Healthy"

            df["Status"] = df.apply(stock_status, axis=1)

            display_cols = ["id", "sku", "name", "category", "cost_price", "sale_price", "stock_quantity", "low_stock_threshold", "Status"]
            df_display = df[display_cols].copy()
            df_display.columns = ["ID", "SKU", "Product Name", "Category", "Cost ($)", "Price ($)", "Stock", "Threshold", "Status"]

            st.dataframe(df_display, hide_index=True, use_container_width=True)

            # Edit & Delete Expander
            with st.expander("✏️ Quick Edit / Deactivate Product"):
                selected_prod_id = st.selectbox(
                    "Select Product to Modify",
                    options=[p["id"] for p in prods],
                    format_func=lambda pid: next((f"{p['sku']} - {p['name']}" for p in prods if p["id"] == pid), str(pid))
                )

                selected_prod = next((p for p in prods if p["id"] == selected_prod_id), None)
                if selected_prod:
                    e_col1, e_col2 = st.columns(2)
                    with e_col1:
                        e_name = st.text_input("Name", value=selected_prod["name"])
                        e_category = st.text_input("Category", value=selected_prod["category"])
                        e_cost = st.number_input("Cost Price ($)", value=float(selected_prod["cost_price"]), min_value=0.0)
                    with e_col2:
                        e_price = st.number_input("Sale Price ($)", value=float(selected_prod["sale_price"]), min_value=0.0)
                        e_threshold = st.number_input("Low Stock Threshold", value=int(selected_prod["low_stock_threshold"]), min_value=0)
                        e_active = st.checkbox("Active for Sale", value=selected_prod["is_active"])

                    u_btn, d_btn = st.columns([1, 1])
                    with u_btn:
                        if st.button("💾 Save Changes", type="primary"):
                            update_payload = {
                                "name": e_name,
                                "category": e_category,
                                "cost_price": e_cost,
                                "sale_price": e_price,
                                "low_stock_threshold": e_threshold,
                                "is_active": e_active
                            }
                            u_ok, u_res = api.update_product(selected_prod_id, update_payload)
                            if u_ok:
                                st.success("Product updated successfully!")
                                st.rerun()
                            else:
                                st.error(f"Update failed: {u_res}")
                    with d_btn:
                        if st.button("🗑️ Deactivate / Delete"):
                            d_ok, d_res = api.delete_product(selected_prod_id, hard_delete=False)
                            if d_ok:
                                st.warning("Product deactivated.")
                                st.rerun()
                            else:
                                st.error(f"Action failed: {d_res}")
        else:
            st.info("No products match the selected criteria.")

    # TAB 2: Add New Product Form
    with tab_add:
        st.subheader("➕ Register New Product")
        with st.form("add_product_form", clear_on_submit=True):
            a_c1, a_c2 = st.columns(2)
            with a_c1:
                n_sku = st.text_input("SKU (Unique Code) *", placeholder="e.g. ELEC-5001")
                n_name = st.text_input("Product Name *", placeholder="e.g. USB-C Multiport Hub")
                n_category = st.text_input("Category", value="General")
                n_barcode = st.text_input("Barcode (Optional)", placeholder="e.g. 194644049999")
            with a_c2:
                n_cost = st.number_input("Cost Price ($)", min_value=0.0, value=10.0, step=0.5)
                n_price = st.number_input("Sale Price ($) *", min_value=0.0, value=19.99, step=0.5)
                n_stock = st.number_input("Initial Stock Quantity", min_value=0, value=20, step=1)
                n_threshold = st.number_input("Low Stock Threshold Alert", min_value=0, value=5, step=1)

            submit_prod = st.form_submit_button("🚀 Create Product", type="primary")

            if submit_prod:
                if not n_sku or not n_name:
                    st.error("SKU and Product Name are required!")
                else:
                    new_prod_payload = {
                        "sku": n_sku.strip(),
                        "name": n_name.strip(),
                        "category": n_category.strip(),
                        "barcode": n_barcode.strip() if n_barcode else None,
                        "cost_price": n_cost,
                        "sale_price": n_price,
                        "stock_quantity": n_stock,
                        "low_stock_threshold": n_threshold,
                        "is_active": True
                    }
                    create_ok, res = api.create_product(new_prod_payload)
                    if create_ok:
                        st.success(f"Product '{n_name}' added successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to create product: {res}")

    # TAB 3: Stock Adjustment (Restock / Damage)
    with tab_adjust:
        st.subheader("⚖️ Inventory Stock Adjustment")
        st.caption("Perform physical stock count corrections, receive restock batches, or record damaged items.")

        ok_all_prods, all_prods = api.get_products(limit=300)
        if ok_all_prods and all_prods:
            adj_prod_id = st.selectbox(
                "Select Product for Stock Adjustment",
                options=[p["id"] for p in all_prods],
                format_func=lambda pid: next((f"{p['sku']} - {p['name']} (Current Stock: {p['stock_quantity']})" for p in all_prods if p["id"] == pid), str(pid))
            )

            adj_c1, adj_c2 = st.columns(2)
            with adj_c1:
                change_qty = st.number_input(
                    "Quantity to Add / Deduct",
                    value=10,
                    step=1,
                    help="Use positive numbers to add inventory, negative numbers to write-off damaged or lost goods."
                )
            with adj_c2:
                adj_reason = st.selectbox("Reason", ["Restock Shipment", "Inventory Audit Correction", "Damaged / Broken", "Returned Item", "Other"])

            if st.button("Apply Stock Adjustment", type="primary"):
                adj_ok, adj_res = api.adjust_stock(adj_prod_id, change_qty, adj_reason)
                if adj_ok:
                    st.success(f"Stock adjusted! New stock quantity: {adj_res['stock_quantity']}")
                    st.rerun()
                else:
                    st.error(f"Adjustment failed: {adj_res}")


# =========================================================================
# 4. CUSTOMER MANAGEMENT
# =========================================================================
elif nav_choice == "👥 Customer Profiles":
    st.title("👥 Customer & Loyalty Management")

    cust_tab1, cust_tab2 = st.tabs(["📋 Customer Directory", "➕ Add Customer"])

    with cust_tab1:
        c_search = st.text_input("🔍 Search Customers (Name, Phone, Email)", placeholder="Search...")
        ok_c, customer_list = api.get_customers(search=c_search if c_search else None)

        if ok_c and customer_list:
            df_cust = pd.DataFrame(customer_list)
            df_cust["Member Since"] = pd.to_datetime(df_cust["created_at"]).dt.strftime("%Y-%m-%d")
            display_cols = ["id", "name", "phone", "email", "loyalty_points", "total_sales_count", "total_spend", "Member Since"]
            df_cust_view = df_cust[display_cols].copy()
            df_cust_view.columns = ["ID", "Customer Name", "Phone", "Email", "Loyalty Pts", "Orders", "Total Spend ($)", "Member Since"]
            st.dataframe(df_cust_view, hide_index=True, use_container_width=True)

            # Customer History View
            with st.expander("🔍 View Customer Order History"):
                target_cid = st.selectbox(
                    "Select Customer",
                    options=[c["id"] for c in customer_list],
                    format_func=lambda cid: next((c["name"] for c in customer_list if c["id"] == cid), str(cid))
                )
                s_ok, cust_sales = api.get_sales(customer_id=target_cid)
                if s_ok and cust_sales:
                    df_csales = pd.DataFrame(cust_sales)
                    df_csales["Date"] = pd.to_datetime(df_csales["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
                    st.dataframe(df_csales[["invoice_no", "total_amount", "payment_method", "status", "Date"]], hide_index=True, use_container_width=True)
                else:
                    st.info("No purchase history found for this customer.")
        else:
            st.info("No customers found.")

    with cust_tab2:
        st.subheader("➕ Register New Customer")
        with st.form("new_customer_form", clear_on_submit=True):
            cn_name = st.text_input("Full Name *", placeholder="Jane Doe")
            cn_phone = st.text_input("Phone Number", placeholder="+1-555-0199")
            cn_email = st.text_input("Email Address", placeholder="jane@example.com")
            cn_points = st.number_input("Starting Loyalty Points", min_value=0, value=0)

            c_submit = st.form_submit_button("Register Customer", type="primary")

            if c_submit:
                if not cn_name:
                    st.error("Customer name is required!")
                else:
                    cust_payload = {
                        "name": cn_name.strip(),
                        "phone": cn_phone.strip() if cn_phone else None,
                        "email": cn_email.strip() if cn_email else None,
                        "loyalty_points": cn_points
                    }
                    create_ok, c_res = api.create_customer(cust_payload)
                    if create_ok:
                        st.success(f"Customer '{cn_name}' created successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to create customer: {c_res}")
