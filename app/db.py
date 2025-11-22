import os
from urllib.parse import urlparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Generator

try:
    # Ensure .env is loaded regardless of CWD (e.g., when Alembic runs from migrations/)
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv(usecwd=True), override=False)
except Exception:
    pass

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

# Enforce Neon/PostgreSQL only
if not SQLALCHEMY_DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Please set a Neon Postgres URL in your .env, e.g. "
        "postgresql+psycopg2://<USER>:<PASSWORD>@<HOST>:5432/<DB>?sslmode=require"
    )

parsed = urlparse(SQLALCHEMY_DATABASE_URL)
if not parsed.scheme.startswith("postgresql"):
    raise RuntimeError(
        f"Unsupported DATABASE_URL scheme '{parsed.scheme}'. This application only supports Postgres/Neon."
    )

# Ensure sslmode=require for Neon if not already present
if "sslmode=" not in SQLALCHEMY_DATABASE_URL and parsed.scheme.startswith("postgresql"):
    sep = "&" if "?" in SQLALCHEMY_DATABASE_URL else "?"
    SQLALCHEMY_DATABASE_URL = f"{SQLALCHEMY_DATABASE_URL}{sep}sslmode=require"

# Serverless-friendly engine options for Neon
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    future=True,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency function to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
