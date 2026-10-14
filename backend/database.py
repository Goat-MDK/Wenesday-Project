import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import settings

logger = logging.getLogger(__name__)

# Determine if connecting to SQLite or PostgreSQL / Neon
db_url = settings.DATABASE_URL
is_sqlite = db_url.startswith("sqlite")
is_postgres = "postgresql" in db_url

connect_args = {}
engine_kwargs = {
    "echo": False,
}

if is_sqlite:
    connect_args["check_same_thread"] = False
elif is_postgres:
    # Neon Serverless Postgres requires SSL connection
    # Ensure sslmode=require is either in the query params or connect_args
    if "sslmode" not in db_url:
        connect_args["sslmode"] = "require"

    # Neon connection pool considerations:
    # 1. pool_pre_ping: Critical for serverless. Discard dead connections when Neon wakes up.
    # 2. pool_recycle: Prevent stale connections after idle timeouts (reconnect every 5 mins).
    # 3. pool_size and max_overflow: sensible limits for pooled database connections.
    engine_kwargs.update({
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 10,
        "max_overflow": 20,
    })

engine = create_engine(
    db_url,
    connect_args=connect_args,
    **engine_kwargs
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    """FastAPI dependency to provide a transactional database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all database tables based on declarative models."""
    from backend import models  # noqa: F401 - ensure models are imported
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")
