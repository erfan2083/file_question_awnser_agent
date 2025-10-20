"""
Wrapper for creating/loading a FAISS vectorstore with OpenAI embeddings.
This centralizes persistence and retrieval functions.
We also ensure every chunk has a unique 'chunk_id' metadata used by Whoosh.
"""
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from typing import List
from pathlib import Path
from config import VECTORSTORE_PATH, CHUNK_SIZE, CHUNK_OVERLAP, OPENAI_API_KEY
import uuid

def docs_to_chunks(documents: List[Document]):
    """
    Split documents into chunks using RecursiveCharacterTextSplitter.
    Adds a unique chunk_id to each chunk's metadata to enable cross-index lookups.
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    split_docs = splitter.split_documents(documents)
    # assign a unique chunk_id to each chunk
    for i, d in enumerate(split_docs):
        if "chunk_id" not in d.metadata:
            # Example id: uuid to ensure uniqueness across uploads/files
            d.metadata["chunk_id"] = str(uuid.uuid4())
    return split_docs

def create_or_load_vectorstore(docs: List[Document], persist: bool = True) -> FAISS:
    """
    Create a new FAISS store from documents or load existing and add docs.
    Returns the FAISS object.
    """
    VECTORSTORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    if VECTORSTORE_PATH.exists():
        # load existing index and add documents
        db = FAISS.load_local(str(VECTORSTORE_PATH), embeddings)
        if docs:
            db.add_documents(docs)
            if persist:
                db.save_local(str(VECTORSTORE_PATH))
        return db
    else:
        db = FAISS.from_documents(docs, embeddings)
        if persist:
            db.save_local(str(VECTORSTORE_PATH))
        return db
