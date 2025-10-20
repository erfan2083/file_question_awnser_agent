from pydantic import BaseModel
from typing import List, Optional

class QueryRequest(BaseModel):
    """
    Pydantic model for the JSON body of a /query request.
    """
    query: str

class Source(BaseModel):
    """
    Pydantic model representing a single cited source.
    """
    filename: str
    page: Optional[int] = None
    # line: Optional[int] = None # Line-level citation is complex; page is more robust.

class QueryResponse(BaseModel):
    """
    Pydantic model for the JSON response of a /query request.
    """
    answer: str
    sources: List[Source]

class UploadResponse(BaseModel):
    """
    Pydantic model for the JSON response of a /upload request.
    """
    message: str
    files_processed: List[str]