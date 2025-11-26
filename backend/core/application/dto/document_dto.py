"""
Data Transfer Objects for documents.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class DocumentUploadDTO:
    """DTO for document upload."""
    title: str
    file_path: str
    file_type: str
    file_size: int
    language: Optional[str] = None


@dataclass
class DocumentDTO:
    """DTO for document output."""
    id: int
    title: str
    file_path: str
    file_type: str
    file_size: int
    status: str
    language: Optional[str]
    error_message: Optional[str]
    num_chunks: int
    num_pages: int
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime]


@dataclass
class DocumentProcessingResultDTO:
    """DTO for document processing result."""
    document_id: int
    success: bool
    num_chunks: int = 0
    num_pages: int = 0
    error_message: Optional[str] = None
