"""Health check endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint.
    Returns API and database status.
    """
    db_status = "healthy"
    db_error = None
    
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = "unhealthy"
        db_error = str(e)
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "api": "healthy",
        "database": db_status,
        "database_error": db_error,
        "version": "1.0.0"
    }
