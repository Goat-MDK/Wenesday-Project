# ⚡ E-Sale Management System

A production-grade, full-stack Point of Sale (POS) & Inventory Management System built with **FastAPI**, **Neon PostgreSQL (Serverless)**, **SQLAlchemy 2.0 ORM**, **Alembic**, and a pure Python **Streamlit Web UI**.

---

## 🛠️ Architecture & Tech Stack

| Layer | Technology | Key Highlights |
| :--- | :--- | :--- |
| **Backend API** | [FastAPI](https://fastapi.tiangolo.com/) | RESTful API, asynchronous performance, automatic OpenAPI / Swagger UI |
| **Database** | [Neon PostgreSQL](https://neon.tech/) | Serverless Postgres with SSL connection & serverless connection pool management |
| **ORM & Migrations** | [SQLAlchemy 2.0](https://www.sqlalchemy.org/) & [Alembic](https://alembic.sqlalchemy.org/) | Type-safe declarative models, auto-migrations, atomic transactions |
| **Validation** | [Pydantic v2](https://docs.pydantic.dev/) | Strict input/output schema validation |
| **Frontend UI** | [Streamlit](https://streamlit.io/) | Pure Python responsive UI with interactive KPI charts, POS cart, and inventory tables |
| **API Client** | `requests` session wrapper | Resilient HTTP wrapper communicating between Streamlit and FastAPI |

---

## 📂 Modular Project Structure

```text
e_sale management system/
│
├── backend/
│   ├── __init__.py
│   ├── config.py              # Environment variables & Neon DB URL normalization
│   ├── database.py            # SQLAlchemy engine (SSL require, pool_pre_ping) & SessionLocal
│   ├── models/                # SQLAlchemy ORM database models
│   │   ├── __init__.py
│   │   ├── product.py         # Product table (SKU, barcode, prices, stock, alerts)
│   │   ├── customer.py        # Customer table (name, phone, loyalty points)
│   │   └── sale.py            # Sale & SaleItem tables (invoice, tax, discount, items)
│   ├── schemas/               # Pydantic validation schemas
│   │   ├── __init__.py
│   │   ├── product.py         # Product request/response schemas
│   │   ├── customer.py        # Customer schemas
│   │   ├── sale.py            # POS checkout request & receipt schemas
│   │   └── analytics.py       # KPI metrics & trend schemas
│   ├── routers/               # FastAPI route controllers
│   │   ├── __init__.py
│   │   ├── products.py        # /api/v1/products (CRUD, live stock check, stock adjustment)
│   │   ├── customers.py       # /api/v1/customers (Profiles, loyalty tracking)
│   │   ├── sales.py           # /api/v1/sales (Atomic checkout, invoice lookup, refunds)
│   │   └── analytics.py       # /api/v1/analytics (KPI summary, top products, 14-day trends)
│   └── main.py                # FastAPI initialization, CORS middleware, lifespan
│
├── frontend/
│   ├── __init__.py
│   ├── api_client.py          # Pure Python REST API client with error handling
│   └── app.py                 # Multi-view Streamlit UI (Dashboard, POS, Inventory, Customers)
│
├── alembic/                   # Database migration scripts
│   ├── env.py                 # Alembic runner with dynamic DB URL & model discovery
│   └── versions/              # Migration versions (9c0574930928_initial_schema.py)
│
├── alembic.ini                # Alembic configuration file
├── seed_data.py               # Database seeder (sample products, customers, and transactions)
├── requirements.txt           # Python package dependencies
├── .env.example               # Template environment configuration
└── .env                       # Active environment configuration
```

---

## 🚀 Step-by-Step Setup & Launch Guide

### Step 1: Install Dependencies
Open PowerShell or your terminal in the `e_sale management system` folder:
```powershell
pip install -r requirements.txt
```

---

### Step 2: Configure Neon PostgreSQL in `.env`
1. Go to [Neon Console](https://console.neon.tech/) and create a project (free tier available).
2. Copy your PostgreSQL connection string:
   ```text
   postgresql://username:password@ep-your-endpoint.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
3. Open `.env` (or copy `.env.example` to `.env`) and paste your URI:
   ```ini
   DATABASE_URL=postgresql://username:password@ep-your-endpoint.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
> **Note on Neon Serverless Compatibility**:
> - Neon requires SSL connections (`?sslmode=require`). The backend automatically enforces SSL.
> - Neon serverless compute sleeps when idle. `backend/database.py` includes `pool_pre_ping=True` and `pool_recycle=300` to automatically heal connections and avoid disconnect errors.
> - If `DATABASE_URL` is omitted, the app will gracefully fall back to local SQLite (`esale_dev.db`) for immediate offline testing.

---

### Step 3: Run Database Migrations
Apply the initial schema to create all tables and indexes:
```powershell
alembic upgrade head
```

---

### Step 4: Seed Initial Sample Data (Optional but Recommended)
Populate the database with realistic products (electronics, accessories, office supplies with low-stock examples), registered customers, and past sales:
```powershell
python seed_data.py
```

---

### Step 5: Launch FastAPI Backend Server
Start the Uvicorn ASGI server:
```powershell
uvicorn backend.main:app --reload --port 8000
```
- **API Base URL**: `http://127.0.0.1:8000`
- **Interactive Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc Documentation**: `http://127.0.0.1:8000/redoc`

---

### Step 6: Launch Streamlit Frontend UI
In a second terminal window:
```powershell
streamlit run frontend/app.py --server.port 8501
```
The browser will automatically open: `http://localhost:8501`

---

## 🌟 Core Features Walkthrough

### 1. 📊 Executive Dashboard & Analytics
- **KPI Cards**: Real-time Gross Revenue, Net Profit, Average Order Value (AOV), and Low Stock Alerts.
- **Trend Visualizations**: Interactive 14-day Line Chart tracking daily revenue vs. profit.
- **Payment Distribution**: Breakdown of revenue and order volume by Cash, Card, and Digital Transfer.
- **Top-Selling Ranking**: Automatically ranks bestsellers by total units sold and revenue.

### 2. 🛒 POS Checkout & Cashier Register
- **Dynamic Catalog**: Filter by category or search by Name, SKU, or Barcode in real-time.
- **Live Inventory Guard**: Badges indicate `IN STOCK`, `LOW STOCK`, or disabled `OUT OF STOCK`.
- **Interactive Cart**: Stepper buttons (`+` / `-`) to adjust quantities with stock limits check.
- **Customer Linking**: Link to registered customer to accumulate loyalty points, or select Walk-in.
- **Discounts & Tax**: Flexible custom discount deduction and tax rate presets (0%, 5%, 10%).
- **Atomic Checkout**: Backend ensures simultaneous stock deduction and sale recording. If stock is insufficient, transaction safely rolls back.
- **Printable Receipt**: Generates a formatted receipt invoice with invoice number, breakdown, and points earned.

### 3. 📦 Inventory Management
- **Directory Table**: Full inventory status with search, sorting, and low-stock filtering.
- **Add Product Form**: Input SKU, barcode, cost, selling price, stock, and alert thresholds.
- **Edit & Deactivate**: Modify prices or soft-deactivate products without losing sales history.
- **Stock Adjustments**: Add restock shipments or record damaged goods with audit reason notes.

### 4. 👥 Customer Management
- **Customer Directory**: View customer profiles, phone numbers, emails, and accumulated loyalty points.
- **Purchase History**: Select any customer to view their previous invoice receipts and order dates.

---

## 📡 REST API Reference Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/products` | List all products with search, category, and low-stock filters |
| `POST` | `/api/v1/products` | Create a new product (validates unique SKU and barcode) |
| `GET` | `/api/v1/products/{id}` | Get product details |
| `PUT` | `/api/v1/products/{id}` | Update product information |
| `DELETE` | `/api/v1/products/{id}` | Deactivate or delete product |
| `GET` | `/api/v1/products/{id}/stock` | Real-time stock status check |
| `POST` | `/api/v1/products/{id}/adjust-stock` | Manual stock adjustment (restock / write-off) |
| `GET` | `/api/v1/customers` | Search & list customer profiles |
| `POST` | `/api/v1/customers` | Register a new customer |
| `GET` | `/api/v1/customers/{id}` | Customer profile with total spend and purchase count |
| `POST` | `/api/v1/sales` | **Atomic POS Checkout**: Deducts inventory, awards loyalty points, creates invoice |
| `GET` | `/api/v1/sales` | List historical sales transactions with filters |
| `GET` | `/api/v1/sales/{id_or_invoice}` | Full sales receipt details |
| `POST` | `/api/v1/sales/{id}/refund` | Refund transaction and replenish inventory |
| `GET` | `/api/v1/analytics/summary` | Overall KPI summary (Revenue, Cost, Profit, Low stock count) |
| `GET` | `/api/v1/analytics/top-products` | Top selling products ranking |
| `GET` | `/api/v1/analytics/trends` | Daily revenue and profit trend series |
| `GET` | `/api/v1/analytics/dashboard` | Consolidated dashboard payload |
#   W e n e s d a y - P r o j e c t  
 