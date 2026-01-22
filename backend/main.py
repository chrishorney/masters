"""
Railway entry point - imports the FastAPI app from app.main
This allows Railway to auto-detect and start the FastAPI application.
"""
from app.main import app

# Railway will detect this as a FastAPI app and use uvicorn automatically
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
