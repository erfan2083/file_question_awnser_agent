import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.core.config import settings
from app.services.retrieval import load_hybrid_retriever

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Local Hybrid RAG QA System",
    description="A multi-agent QA system with hybrid retrieval.",
    version="1.0.0"
)

# CORS (Cross-Origin Resource Sharing) Middleware
# This allows the React frontend (running on a different port)
# to communicate with the backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    """
    Startup event handler.
    - Creates necessary data directories.
    - Attempts to load an existing retriever from disk.
    """
    logger.info("Application starting up...")
    
    # Create data directories if they don't exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.VECTORSTORE_DIR, exist_ok=True)
    logger.info("Data directories ensured.")
    
    # Try to load the retriever on startup
    try:
        load_hybrid_retriever()
    except Exception as e:
        logger.error(f"Failed to load retriever on startup: {e}. "
                     "This is normal if no documents have been uploaded yet.")

# Include the API router
app.include_router(api_router)

@app.get("/", tags=["Root"])
async def read_root():
    """
    Root endpoint. Provides basic info and a link to the docs.
    """
    return {
        "message": "Welcome to the Local Hybrid RAG API. See /docs for details."
    }