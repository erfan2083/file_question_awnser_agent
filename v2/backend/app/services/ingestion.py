import os
import logging
from typing import List
from fastapi import UploadFile
from PIL import Image
import pytesseract

from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    TextLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document

from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom loader for images using Tesseract OCR
class ImageLoader:
    """Loads image files and extracts text using Tesseract OCR."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self) -> List[Document]:
        """Loads image and performs OCR."""
        try:
            image = Image.open(self.file_path)
            text = pytesseract.image_to_string(image)
            if not text.strip():
                logger.warning(f"No text extracted from image: {self.file_path}")
                return []
                
            filename = os.path.basename(self.file_path)
            metadata = {"source": filename, "page": 1} # Treat image as a single page
            return [Document(page_content=text, metadata=metadata)]
        except Exception as e:
            logger.error(f"Error processing image {self.file_path}: {e}")
            return []

def get_document_loader(file_path: str, extension: str) -> PyPDFLoader | UnstructuredWordDocumentLoader | TextLoader | ImageLoader | None:
    """
    Returns the appropriate LangChain DocumentLoader based on the file extension.
    """
    if extension == ".pdf":
        return PyPDFLoader(file_path)
    elif extension == ".docx":
        return UnstructuredWordDocumentLoader(file_path)
    elif extension == ".txt":
        return TextLoader(file_path)
    elif extension in [".png", ".jpg", ".jpeg"]:
        return ImageLoader(file_path)
    else:
        logger.warning(f"Unsupported file type: {extension}. Skipping.")
        return None

def load_and_split_documents(file_paths: List[str]) -> List[Document]:
    """
    Loads all documents from the provided file paths and splits them into chunks.
    
    Args:
        file_paths: A list of absolute paths to the saved files.

    Returns:
        A list of Document chunks ready for embedding.
    """
    all_docs = []
    for file_path in file_paths:
        try:
            _, extension = os.path.splitext(file_path)
            extension = extension.lower()
            
            loader = get_document_loader(file_path, extension)
            if loader:
                logger.info(f"Loading document: {file_path}")
                docs = loader.load()
                # Ensure 'source' metadata points to the original filename, not the temp path
                filename = os.path.basename(file_path)
                for doc in docs:
                    doc.metadata["source"] = filename
                all_docs.extend(docs)
        except Exception as e:
            logger.error(f"Failed to load or process {file_path}: {e}", exc_info=True)

    if not all_docs:
        logger.warning("No documents were successfully loaded.")
        return []

    # Initialize the text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP
    )
    
    # Split the documents into chunks
    logger.info(f"Splitting {len(all_docs)} loaded documents into chunks...")
    chunks = text_splitter.split_documents(all_docs)
    logger.info(f"Created {len(chunks)} chunks.")
    
    return chunks

async def process_uploaded_files(files: List[UploadFile]) -> List[Document]:
    """
    Saves uploaded files, then loads and chunks them.
    
    Args:
        files: A list of files from the FastAPI endpoint.

    Returns:
        A list of Document chunks.
    """
    saved_file_paths = []
    
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    for file in files:
        file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
        
        # Save the file
        try:
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())
            saved_file_paths.append(file_path)
            logger.info(f"Successfully saved file: {file.filename}")
        except Exception as e:
            logger.error(f"Failed to save file {file.filename}: {e}")

    # Process the saved files
    if not saved_file_paths:
        return []
        
    chunks = load_and_split_documents(saved_file_paths)
    return chunks