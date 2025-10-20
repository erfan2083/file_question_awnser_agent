import pytest
from unittest.mock import patch, MagicMock
from app.services.ingestion import get_document_loader, load_and_split_documents
from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader, TextLoader
from app.services.ingestion import ImageLoader

def test_get_document_loader():
    """Tests the loader factory function."""
    
    # PDF
    loader = get_document_loader("test.pdf", ".pdf")
    assert isinstance(loader, PyPDFLoader)
    
    # DOCX
    loader = get_document_loader("test.docx", ".docx")
    assert isinstance(loader, UnstructuredWordDocumentLoader)
    
    # TXT
    loader = get_document_loader("test.txt", ".txt")
    assert isinstance(loader, TextLoader)
    
    # Image
    loader = get_document_loader("test.png", ".png")
    assert isinstance(loader, ImageLoader)
    loader = get_document_loader("test.jpg", ".jpg")
    assert isinstance(loader, ImageLoader)
    
    # Unsupported
    loader = get_document_loader("test.xls", ".xls")
    assert loader is None

@patch('app.services.ingestion.get_document_loader')
@patch('app.services.ingestion.RecursiveCharacterTextSplitter')
def test_load_and_split_documents(MockTextSplitter, mock_get_loader):
    """
    Tests the main document loading and splitting pipeline.
    """
    # --- Setup Mocks ---
    
    # 1. Mock the loader factory
    mock_pdf_loader_inst = MagicMock(spec=PyPDFLoader)
    mock_txt_loader_inst = MagicMock(spec=TextLoader)
    
    # Mock the .load() method of the loader instances
    doc1 = MagicMock(metadata={"source": "temp_doc1.pdf", "page": 1})
    doc1.page_content = "This is PDF page 1."
    doc2 = MagicMock(metadata={"source": "temp_doc1.pdf", "page": 2})
    doc2.page_content = "This is PDF page 2."
    doc3 = MagicMock(metadata={"source": "temp_doc2.txt"})
    doc3.page_content = "This is a text file."
    
    mock_pdf_loader_inst.load.return_value = [doc1, doc2]
    mock_txt_loader_inst.load.return_value = [doc3]

    # Configure the factory to return our mocked instances
    def loader_side_effect(file_path, extension):
        if extension == ".pdf":
            return mock_pdf_loader_inst
        if extension == ".txt":
            return mock_txt_loader_inst
        return None
    mock_get_loader.side_effect = loader_side_effect

    # 2. Mock the text splitter
    mock_splitter_inst = MockTextSplitter.return_value
    # Let's say it splits doc1 and doc2, but doc3 is small enough
    chunk1 = MagicMock(metadata={"source": "doc1.pdf", "page": 1})
    chunk2 = MagicMock(metadata={"source": "doc1.pdf", "page": 2})
    chunk3 = MagicMock(metadata={"source": "doc2.txt"})
    
    mock_splitter_inst.split_documents.return_value = [chunk1, chunk2, chunk3]

    # --- Run Test ---
    file_paths = ["/path/to/doc1.pdf", "/path/to/doc2.txt"]
    chunks = load_and_split_documents(file_paths)

    # --- Assertions ---
    
    # Check that loaders were called
    mock_pdf_loader_inst.load.assert_called_once()
    mock_txt_loader_inst.load.assert_called_once()
    
    # Check that metadata 'source' was correctly overwritten
    assert doc1.metadata["source"] == "doc1.pdf"
    assert doc2.metadata["source"] == "doc1.pdf"
    assert doc3.metadata["source"] == "doc2.txt"

    # Check that splitter was called with the combined docs
    mock_splitter_inst.split_documents.assert_called_once_with([doc1, doc2, doc3])
    
    # Check final output
    assert len(chunks) == 3
    assert chunks[0].metadata["source"] == "doc1.pdf"
    assert chunks[2].metadata["source"] == "doc2.txt"

@patch('app.services.ingestion.pytesseract')
@patch('app.services.ingestion.Image.open')
def test_image_loader(mock_image_open, mock_pytesseract):
    """Tests the custom ImageLoader."""
    
    # Setup mocks
    mock_img = MagicMock()
    mock_image_open.return_value = mock_img
    mock_pytesseract.image_to_string.return_value = "This is text from an image."
    
    # Test
    loader = ImageLoader("/path/to/image.png")
    docs = loader.load()
    
    # Assert
    mock_image_open.assert_called_with("/path/to/image.png")
    mock_pytesseract.image_to_string.assert_called_with(mock_img)
    
    assert len(docs) == 1
    assert docs[0].page_content == "This is text from an image."
    assert docs[0].metadata["source"] == "image.png"
    assert docs[0].metadata["page"] == 1