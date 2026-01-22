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
    # Create tables (in production, use migrations)
    if settings.environment == "development":
        Base.metadata.create_all(bind=engine)
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


# Import and include routers (will be added in later phases)
# from app.api.public import leaderboard, entries
# from app.api.admin import auth, imports
# app.include_router(leaderboard.router, prefix=settings.api_prefix, tags=["public"])
# app.include_router(entries.router, prefix=settings.api_prefix, tags=["public"])
# app.include_router(auth.router, prefix=f"{settings.api_prefix}/admin", tags=["admin"])
# app.include_router(imports.router, prefix=f"{settings.api_prefix}/admin", tags=["admin"])
