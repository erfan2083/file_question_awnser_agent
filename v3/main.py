"""FastAPI application for Document QA System."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import List, Optional

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel

from src.agents.orchestrator import MultiAgentOrchestrator
from src.config.settings import settings
from src.document_processing import DocumentIndexer, chunk_document, load_document
from src.models.schemas import Answer, UtilityTask

# Initialize FastAPI app
app = FastAPI(
    title="Document QA System",
    description="Intelligent Document Question Answering System with Multi-Agent Orchestration",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
orchestrator = MultiAgentOrchestrator()
retriever_agent, reasoning_agent, utility_agent = orchestrator.get_agents()
indexer = retriever_agent.get_retriever().get_retrievers()[0].get_indexer()

# Store for BM25 retriever
bm25_retriever = retriever_agent.get_retriever().get_retrievers()[1]

# Request/Response models
class QuestionRequest(BaseModel):
    question: str
    document_id: Optional[str] = None


class UtilityRequest(BaseModel):
    task: str
    text: Optional[str] = None
    question: Optional[str] = None
    target_language: Optional[str] = "es"


class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    num_chunks: int
    message: str


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Document QA System API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "document-qa-system"}


@app.post("/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and index a document.

    Args:
        file: Document file to upload

    Returns:
        Document metadata
    """
    try:
        # Check file size
        contents = await file.read()
        if len(contents) > settings.max_upload_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size: {settings.max_upload_size} bytes",
            )

        # Load document
        text, metadata = load_document(file.filename, contents)

        # Chunk document
        chunks = chunk_document(text, metadata)

        # Index chunks
        indexer.index_chunks(chunks, metadata)

        # Index for BM25
        bm25_retriever.index_chunks(chunks)

        logger.info(f"Successfully uploaded and indexed document: {file.filename}")

        return DocumentResponse(
            document_id=metadata.document_id,
            filename=metadata.filename,
            num_chunks=len(chunks),
            message="Document uploaded and indexed successfully",
        )

    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask", response_model=Answer)
async def ask_question(request: QuestionRequest):
    """
    Ask a question about uploaded documents.

    Args:
        request: Question request

    Returns:
        Answer object
    """
    try:
        answer = orchestrator.answer_question(
            question=request.question, document_id=request.document_id
        )

        logger.info(f"Successfully answered question: {request.question}")

        return answer

    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/utility")
async def perform_utility_task(request: UtilityRequest):
    """
    Perform a utility task.

    Args:
        request: Utility request

    Returns:
        Task result
    """
    try:
        # Convert task string to enum
        task = UtilityTask(request.task)

        result = orchestrator.perform_utility_task(
            task=task,
            text=request.text,
            question=request.question,
            target_language=request.target_language,
        )

        logger.info(f"Successfully performed utility task: {request.task}")

        return {"task": request.task, "result": result}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid task: {request.task}")
    except Exception as e:
        logger.error(f"Error performing utility task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
async def list_documents():
    """
    List all indexed documents.

    Returns:
        List of document statistics
    """
    try:
        stats = indexer.get_collection_stats()
        return stats
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document from the index.

    Args:
        document_id: Document ID to delete

    Returns:
        Deletion confirmation
    """
    try:
        indexer.delete_document(document_id)
        logger.info(f"Successfully deleted document: {document_id}")
        return {"message": f"Document {document_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset")
async def reset_system():
    """
    Reset the entire system (clear all documents).

    Returns:
        Reset confirmation
    """
    try:
        indexer.reset_collection()
        bm25_retriever.clear()
        logger.info("Successfully reset system")
        return {"message": "System reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting system: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Configure logging
    logger.add(
        "logs/api.log",
        rotation="500 MB",
        retention="10 days",
        level=settings.log_level,
    )

    # Run server
    uvicorn.run(
        app,
        host=settings.app_host,
        port=settings.app_port,
        log_level=settings.log_level.lower(),
    )
