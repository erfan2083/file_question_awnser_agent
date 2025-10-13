"""
High-level ingestion API used by FastAPI endpoint.
Loads a file, splits to chunks, persists embeddings in FAISS.
"""
from pathlib import Path
from utils import load_any
from vectorstore import docs_to_chunks, create_or_load_vectorstore
from langchain.schema import Document
import shutil

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def ingest_file(local_path: str, persist: bool = True):
    """
    Load file from path, convert to Documents, chunk, and index.
    Returns the FAISS db object.
    """
    docs = load_any(local_path)
    chunks = docs_to_chunks(docs)
    db = create_or_load_vectorstore(chunks, persist=persist)
    return db

def save_upload_file(upload_file, destination: str):
    """
    Save FastAPI UploadFile to destination path.
    """
    with open(destination, "wb") as out:
        shutil.copyfileobj(upload_file.file, out)
    return destination
