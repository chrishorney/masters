#!/bin/bash
# Start script for Railway deployment

# Run migrations (ignore errors if already applied)
alembic upgrade head || true

# Start the FastAPI application
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
