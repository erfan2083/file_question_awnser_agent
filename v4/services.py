import os
import pdfplumber
from docx import Document as DocxDocument
from PIL import Image
import google.generativeai as genai
from django.conf import settings
from .models import Document, DocumentChunk
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

# Configure Gemini API
genai.configure(api_key=settings.GOOGLE_API_KEY)


class DocumentIngestionService:
    """Service for document ingestion and processing"""

    def __init__(self):
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
        self.embedding_model = settings.GEMINI_EMBEDDING_MODEL

    def process_document(self, document: Document) -> None:
        """
        Process a document: extract text, chunk it, and generate embeddings
        """
        try:
            document.status = Document.Status.PROCESSING
            document.save()

            # Extract text based on file type
            text, page_info = self._extract_text(document)

            if not text:
                raise ValueError("No text could be extracted from the document")

            # Create chunks
            chunks = self._create_chunks(text, page_info)

            # Store chunks with embeddings
            self._store_chunks(document, chunks)

            document.status = Document.Status.READY
            document.save()

            logger.info(
                f"Successfully processed document {document.id} with {len(chunks)} chunks"
            )

        except Exception as e:
            logger.error(f"Error processing document {document.id}: {str(e)}")
            document.status = Document.Status.FAILED
            document.error_message = str(e)
            document.save()
            raise

    def _extract_text(self, document: Document) -> Tuple[str, List[int]]:
        """Extract text from document based on file type"""
        file_path = document.file.path

        if document.file_type == Document.FileType.PDF:
            return self._extract_from_pdf(file_path)
        elif document.file_type == Document.FileType.DOCX:
            return self._extract_from_docx(file_path)
        elif document.file_type == Document.FileType.TXT:
            return self._extract_from_txt(file_path)
        elif document.file_type in [Document.FileType.JPG, Document.FileType.PNG]:
            return self._extract_from_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {document.file_type}")

    def _extract_from_pdf(self, file_path: str) -> Tuple[str, List[int]]:
        """Extract text from PDF"""
        text = ""
        page_info = []

        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
                    page_info.extend([page_num] * len(page_text.split()))

        return text, page_info

    def _extract_from_docx(self, file_path: str) -> Tuple[str, List[int]]:
        """Extract text from DOCX"""
        doc = DocxDocument(file_path)
        text = "\n\n".join([paragraph.text for paragraph in doc.paragraphs])
        page_info = [1] * len(text.split())  # DOCX doesn't have clear page numbers
        return text, page_info

    def _extract_from_txt(self, file_path: str) -> Tuple[str, List[int]]:
        """Extract text from TXT"""
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        page_info = [1] * len(text.split())
        return text, page_info

    def _extract_from_image(self, file_path: str) -> Tuple[str, List[int]]:
        """Extract text from image using Gemini Vision"""
        try:
            # Load image
            image = Image.open(file_path)

            # Use Gemini for OCR
            model = genai.GenerativeModel("gemini-pro-vision")
            response = model.generate_content(
                ["Extract all text from this image:", image]
            )

            text = response.text if response.text else ""
            page_info = [1] * len(text.split())
            return text, page_info

        except Exception as e:
            logger.error(f"Error extracting text from image: {str(e)}")
            raise

    def _create_chunks(
        self, text: str, page_info: List[int]
    ) -> List[Tuple[str, int]]:
        """Create overlapping text chunks"""
        words = text.split()
        chunks = []
        chunk_words = self.chunk_size // 4  # Approximate words per chunk
        overlap_words = self.chunk_overlap // 4

        for i in range(0, len(words), chunk_words - overlap_words):
            chunk_text = " ".join(words[i : i + chunk_words])
            # Get page number for the middle of the chunk
            mid_point = i + chunk_words // 2
            page_num = page_info[min(mid_point, len(page_info) - 1)] if page_info else 1
            chunks.append((chunk_text, page_num))

        return chunks

    def _store_chunks(self, document: Document, chunks: List[Tuple[str, int]]) -> None:
        """Store chunks with embeddings"""
        for index, (chunk_text, page_num) in enumerate(chunks):
            # Generate embedding
            embedding = self._generate_embedding(chunk_text)

            # Create chunk
            DocumentChunk.objects.create(
                document=document,
                index=index,
                text=chunk_text,
                page_number=page_num,
                embedding=embedding,
            )

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Gemini"""
        try:
            result = genai.embed_content(
                model=self.embedding_model, content=text, task_type="retrieval_document"
            )
            return result["embedding"]
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            # Return zero vector as fallback
            return [0.0] * 768
