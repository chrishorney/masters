"""Test database connection and models."""
import pytest
from sqlalchemy import text
from app.database import engine, get_db


def test_database_connection():
    """Test that database connection works."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


def test_get_db():
    """Test database session dependency."""
    db_gen = get_db()
    db = next(db_gen)
    assert db is not None
    db.close()
