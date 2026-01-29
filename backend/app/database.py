"""Database connection and session management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# Create database engine with connection pool limits
# Supabase connection pooler typically allows 15 connections in session mode
# We'll use a conservative pool size to avoid exhaustion
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=5,  # Number of connections to maintain in the pool
    max_overflow=10,  # Maximum number of connections beyond pool_size
    pool_recycle=3600,  # Recycle connections after 1 hour to prevent stale connections
    pool_timeout=30,  # Timeout when trying to get a connection from the pool
    echo=settings.environment == "development"  # Log SQL queries in dev
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
