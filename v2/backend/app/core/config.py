import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Configuration settings for the application.
    Reads from environment variables or uses default values.
    """
    
    # Model Configuration
    # Note: Using Phi-3-mini as the best-in-class CPU-friendly model 
    # matching the "3b" parameter spec.
    EMBED_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    LLM_MODEL_NAME: str = "microsoft/Phi-3-mini-4k-instruct"
    
    # Path Configuration (relative to the /app directory inside Docker)
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR: str = "/app/data"
    UPLOAD_DIR: str = "/app/data/uploads"
    VECTORSTORE_DIR: str = "/app/data/vectorstore"
    
    # Derived paths
    FAISS_INDEX_PATH: str = os.path.join(VECTORSTORE_DIR, "faiss_index")

    # Chunking Configuration
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # Retrieval Configuration
    RETRIEVER_K: int = 6 # Number of docs to retrieve

    class Config:
        # Allows reading from a .env file if present (though we use Docker envs)
        env_file = ".env"
        env_file_encoding = "utf-8"

# Singleton instance to be imported by other modules
settings = Settings()