"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
import logging

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Create FastAPI app
app = FastAPI(
    title="Eldorado Masters Pool API",
    description="API for managing the Eldorado Masters Golf Tournament pool",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    # Verify database connection
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logging.info("Database connection verified")
    except Exception as e:
        logging.warning(f"Database connection failed: {e}. App will continue but database features may not work.")
    logging.info("Application started")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "environment": settings.environment}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Eldorado Masters Pool API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# Import and include routers
from app.api.public import tournament, scores
from app.api.admin import bonus_points, players, imports
app.include_router(tournament.router, prefix=settings.api_prefix, tags=["tournament"])
app.include_router(scores.router, prefix=settings.api_prefix, tags=["scores"])
app.include_router(bonus_points.router, prefix=f"{settings.api_prefix}/admin", tags=["admin"])
app.include_router(players.router, prefix=f"{settings.api_prefix}/admin", tags=["admin"])
app.include_router(imports.router, prefix=f"{settings.api_prefix}/admin", tags=["admin"])