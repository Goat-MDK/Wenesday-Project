import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)


class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "E-Sale Management System")
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    # Neon PostgreSQL database URL
    # Example format: postgresql://[user]:[password]@[endpoint].neon.tech/[dbname]?sslmode=require
    RAW_DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./esale_dev.db"  # Sensible fallback so app launches immediately out of the box
    )

    # Normalize database URL for SQLAlchemy compatibility
    @property
    def DATABASE_URL(self) -> str:
        url = self.RAW_DATABASE_URL.strip()
        # SQLAlchemy 1.4+ / 2.0 requires postgresql:// instead of postgres://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        # Ensure psycopg2 driver is specified if raw postgresql is provided
        if url.startswith("postgresql://") and not url.startswith("postgresql+"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url

    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8501",  # Streamlit default port
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8501",
        "*"
    ]

    # POS & Financial Defaults
    DEFAULT_TAX_RATE: float = float(os.getenv("DEFAULT_TAX_RATE", "0.05"))  # 5% tax
    LOW_STOCK_DEFAULT_THRESHOLD: int = int(os.getenv("LOW_STOCK_DEFAULT_THRESHOLD", "10"))
    CURRENCY_SYMBOL: str = os.getenv("CURRENCY_SYMBOL", "$")


settings = Settings()
