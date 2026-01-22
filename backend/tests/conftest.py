"""Pytest configuration and fixtures."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.config import settings


@pytest.fixture(scope="function")
def db():
    """Create a database session for testing."""
    # Use the same database URL but create a new engine for tests
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Clean up - drop all tables after test
        Base.metadata.drop_all(bind=engine)
