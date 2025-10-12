"""
Wrapper for creating/loading a FAISS vectorstore with OpenAI embeddings.
This centralizes persistence and retrieval functions.
"""
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from typing import List
from pathlib import Path
from config import VECTORSTORE_PATH, CHUNK_SIZE, CHUNK_OVERLAP, OPENAI_API_KEY

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
        return db
    else:
        db = FAISS.from_documents(docs, embeddings)
        if persist:
            db.save_local(str(VECTORSTORE_PATH))
        return db

def docs_to_chunks(documents: List[Document]):
    """Split documents into chunks using RecursiveCharacterTextSplitter."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    return splitter.split_documents(documents)
