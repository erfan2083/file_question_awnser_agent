import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.models import QueryRequest, QueryResponse, UploadResponse
from app.services.ingestion import process_uploaded_files
from app.services.retrieval import new_retriever_from_docs, get_retriever
from app.services.graph import create_qa_graph

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1",
    tags=["QA System"]
)

# Instantiate the QA graph
try:
    qa_graph = create_qa_graph()
except Exception as e:
    logger.critical(f"Failed to initialize QA graph: {e}", exc_info=True)
    # If the graph (and LLM) fails to load, we can't run the app.
    # In a real-world scenario, you might have a health check,
    # but for this app, we'll let it fail fast on startup.
    raise

@router.post("/upload", response_model=UploadResponse)
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Endpoint to upload one or more documents.
    The files are processed, chunked, embedded, and indexed.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files were uploaded.")
    
    filenames = [f.filename for f in files]
    logger.info(f"Received {len(files)} files for upload: {', '.join(filenames)}")
    
    try:
        # 1. Process files (save, load, chunk)
        chunks = await process_uploaded_files(files)
        
        if not chunks:
            raise HTTPException(status_code=400, detail="No documents could be processed from the uploaded files.")
            
        # 2. Create and save the new retriever
        new_retriever_from_docs(chunks)
        
        logger.info(f"Successfully processed and indexed {len(filenames)} files.")
        return UploadResponse(
            message=f"Successfully processed {len(chunks)} chunks from {len(filenames)} files.",
            files_processed=filenames
        )
    except Exception as e:
        logger.error(f"Error during file upload and processing: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the files: {e}"
        )

@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Endpoint to ask a question to the QA system.
    """
    logger.info(f"Received query: {request.query}")
    
    try:
        # 1. Check if the retriever is initialized
        # This will raise a ValueError if no docs have been uploaded
        get_retriever() 
    except ValueError as e:
        logger.warning("Query received, but no documents are processed.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    try:
        # 2. Run the QA graph
        inputs = {"question": request.query}
        # The graph is stateful and tracks its own progress
        result = qa_graph.invoke(inputs)
        
        logger.info(f"Generated answer with {len(result['sources'])} sources.")
        
        # 3. Return the formatted response
        return QueryResponse(
            answer=result['answer'],
            sources=result['sources']
        )
    except Exception as e:
        logger.error(f"Error during query invocation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating the answer: {e}"
        )

@router.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}