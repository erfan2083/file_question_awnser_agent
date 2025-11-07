"""Document loaders for various file formats."""

import io
from pathlib import Path
from typing import Union

import docx
from loguru import logger
from PIL import Image
from pypdf import PdfReader

try:
    import pytesseract
except ImportError:
    pytesseract = None

from src.models.schemas import DocumentFormat, DocumentMetadata
from src.utils.helpers import clean_text, generate_id


class DocumentLoader:
    """Base class for document loaders."""

    def __init__(self):
        """Initialize document loader."""
        self.supported_formats = {
            ".pdf": DocumentFormat.PDF,
            ".docx": DocumentFormat.DOCX,
            ".txt": DocumentFormat.TXT,
            ".png": DocumentFormat.IMAGE,
            ".jpg": DocumentFormat.IMAGE,
            ".jpeg": DocumentFormat.IMAGE,
        }

    def load(self, file_path: Union[str, Path], file_content: bytes = None) -> tuple[str, DocumentMetadata]:
        """
        Load document from file.

        Args:
            file_path: Path to document file
            file_content: Optional file content as bytes

        Returns:
            Tuple of (document text, metadata)
        """
        file_path = Path(file_path)
        extension = file_path.suffix.lower()

        if extension not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {extension}")

        format_type = self.supported_formats[extension]

        # Load content
        if file_content is None:
            with open(file_path, "rb") as f:
                file_content = f.read()

        # Extract text based on format
        if format_type == DocumentFormat.PDF:
            text = self._load_pdf(file_content)
        elif format_type == DocumentFormat.DOCX:
            text = self._load_docx(file_content)
        elif format_type == DocumentFormat.TXT:
            text = self._load_txt(file_content)
        elif format_type == DocumentFormat.IMAGE:
            text = self._load_image(file_content)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

        # Create metadata
        document_id = generate_id(file_path.name, prefix="doc_")
        metadata = DocumentMetadata(
            document_id=document_id,
            filename=file_path.name,
            format=format_type,
            file_size=len(file_content),
        )

        logger.info(f"Loaded document: {file_path.name} ({format_type}) - {len(text)} characters")

        return clean_text(text), metadata

    def _load_pdf(self, content: bytes) -> str:
        """
        Load PDF document.

        Args:
            content: PDF file content

        Returns:
            Extracted text
        """
        try:
            pdf_file = io.BytesIO(content)
            reader = PdfReader(pdf_file)
            text_parts = []

            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"Error loading PDF: {e}")
            raise

    def _load_docx(self, content: bytes) -> str:
        """
        Load DOCX document.

        Args:
            content: DOCX file content

        Returns:
            Extracted text
        """
        try:
            docx_file = io.BytesIO(content)
            doc = docx.Document(docx_file)
            text_parts = []

            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)

            return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"Error loading DOCX: {e}")
            raise

    def _load_txt(self, content: bytes) -> str:
        """
        Load TXT document.

        Args:
            content: TXT file content

        Returns:
            Extracted text
        """
        try:
            # Try different encodings
            encodings = ["utf-8", "latin-1", "cp1252"]
            for encoding in encodings:
                try:
                    return content.decode(encoding)
                except UnicodeDecodeError:
                    continue
            # If all encodings fail, use utf-8 with error handling
            return content.decode("utf-8", errors="ignore")
        except Exception as e:
            logger.error(f"Error loading TXT: {e}")
            raise

    def _load_image(self, content: bytes) -> str:
        """
        Load image document using OCR.

        Args:
            content: Image file content

        Returns:
            Extracted text via OCR
        """
        if pytesseract is None:
            raise ImportError(
                "pytesseract is required for image processing. " "Install it with: pip install pytesseract"
            )

        try:
            image = Image.open(io.BytesIO(content))
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            raise


def load_document(file_path: Union[str, Path], file_content: bytes = None) -> tuple[str, DocumentMetadata]:
    """
    Convenience function to load a document.

    Args:
        file_path: Path to document file
        file_content: Optional file content as bytes

    Returns:
        Tuple of (document text, metadata)
    """
    loader = DocumentLoader()
    return loader.load(file_path, file_content)
