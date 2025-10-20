import os
import logging
from typing import List, Optional
import torch

from langchain.schema.document import Document
from langchain.schema.retriever import BaseRetriever
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Global Components ---
# We initialize these once to be reused.

def get_embeddings_model():
    """Initializes and returns the HuggingFace embeddings model."""
    # Use CPU device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Initializing embeddings model on device: {device}")
    return HuggingFaceEmbeddings(
        model_name=settings.EMBED_MODEL_NAME,
        model_kwargs={'device': device},
        encode_kwargs={'normalize_embeddings': True}
    )

# Initialize embeddings model globally
embeddings = get_embeddings_model()

# Global variable to hold the retriever instance (singleton pattern)
_ensemble_retriever: Optional[BaseRetriever] = None

def create_hybrid_retriever(docs: List[Document]) -> BaseRetriever:
    """
    Creates a new hybrid ensemble retriever from a list of documents.

    Args:
        docs: A list of Document chunks.

    Returns:
        An configured EnsembleRetriever.
    """
    logger.info("Creating new hybrid retriever...")
    
    # 1. Create FAISS vector store and retriever (Semantic)
    try:
        faiss_vectorstore = FAISS.from_documents(docs, embeddings)
        # Save the FAISS index to disk
        faiss_vectorstore.save_local(settings.FAISS_INDEX_PATH)
        logger.info(f"FAISS index saved to: {settings.FAISS_INDEX_PATH}")
    except Exception as e:
        logger.error(f"Failed to create or save FAISS index: {e}", exc_info=True)
        raise

    faiss_retriever = faiss_vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": settings.RETRIEVER_K}
    )

    # 2. Create BM25 retriever (Lexical)
    # BM25Retriever must be rebuilt from docs each time, as it's not easily serializable
    logger.info("Creating BM25 retriever...")
    bm25_retriever = BM25Retriever.from_documents(docs)
    bm25_retriever.k = settings.RETRIEVER_K

    # 3. Create Ensemble Retriever
    # We give BM25 a slightly lower weight as semantic search is often more powerful
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, faiss_retriever],
        weights=[0.4, 0.6]
    )
    
    logger.info("Hybrid retriever created successfully.")
    return ensemble_retriever

def load_hybrid_retriever() -> Optional[BaseRetriever]:
    """
    Loads an existing hybrid retriever from disk.
    
    - Loads the FAISS index.
    - Extracts the documents from the FAISS docstore.
    - Rebuilds the BM25 retriever from those documents.
    - Creates the ensemble.

    Returns:
        An configured EnsembleRetriever, or None if the index doesn't exist.
    """
    if not os.path.exists(settings.FAISS_INDEX_PATH):
        logger.warning("FAISS index not found. No retriever to load.")
        return None

    logger.info(f"Loading FAISS index from: {settings.FAISS_INDEX_PATH}")
    try:
        # Allow dangerous deserialization for FAISS's internal pickle
        faiss_vectorstore = FAISS.load_local(
            settings.FAISS_INDEX_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )
    except Exception as e:
        logger.error(f"Failed to load FAISS index: {e}. It may be corrupt.", exc_info=True)
        return None

    faiss_retriever = faiss_vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": settings.RETRIEVER_K}
    )

    # Rebuild BM25 retriever from the documents stored in FAISS
    # FAISS.docstore._dict is the internal mapping of {doc_id: Document}
    docs = list(faiss_vectorstore.docstore._dict.values())
    if not docs:
        logger.error("FAISS index loaded, but docstore is empty. Cannot build BM25 retriever.")
        return None
    
    logger.info(f"Rebuilding BM25 retriever from {len(docs)} documents...")
    bm25_retriever = BM25Retriever.from_documents(docs)
    bm25_retriever.k = settings.RETRIEVER_K

    # Create Ensemble Retriever
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, faiss_retriever],
        weights=[0.4, 0.6]
    )
    
    logger.info("Hybrid retriever loaded and rebuilt successfully.")
    return ensemble_retriever

def get_retriever() -> BaseRetriever:
    """
    Main access point for the retriever.
    Returns the singleton instance, loading it from disk if necessary.
    
    Raises:
        ValueError: If no documents have been processed and no index exists.

    Returns:
        The singleton BaseRetriever instance.
    """
    global _ensemble_retriever
    if _ensemble_retriever is None:
        _ensemble_retriever = load_hybrid_retriever()

    if _ensemble_retriever is None:
        raise ValueError("No documents have been processed. Please upload files first.")
        
    return _ensemble_retriever

def new_retriever_from_docs(docs: List[Document]) -> BaseRetriever:
    """
    Builds a new retriever from fresh documents and sets it as the 
    global singleton instance.
    """
    global _ensemble_retriever
    _ensemble_retriever = create_hybrid_retriever(docs)
    return _ensemble_retriever