import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import io

from app.main import app
from app.core.models import QueryResponse, Source

# Use pytest-xdist 'fixture' scope if running in parallel, 
# but 'module' is fine for this project.
@pytest.fixture(scope="module")
def client():
    """
    Test client fixture for making requests to the FastAPI app.
    """
    with TestClient(app) as c:
        yield c

@pytest.fixture(autouse=True)
def mock_services():
    """
    Automatically mock all service-layer dependencies for API tests.
    We are testing the API layer, not the services themselves.
    """
    # Mock ingestion
    with patch('app.api.routes.process_uploaded_files') as mock_process:
        # Mock retrieval
        with patch('app.api.routes.new_retriever_from_docs') as mock_new_retriever:
            # Mock graph
            with patch('app.api.routes.qa_graph') as mock_graph:
                # Mock get_retriever (for the check in /query)
                with patch('app.api.routes.get_retriever') as mock_get_retriever:
                    # Yield all mocks to be used in tests if needed
                    yield {
                        "process": mock_process,
                        "new_retriever": mock_new_retriever,
                        "graph": mock_graph,
                        "get_retriever": mock_get_retriever
                    }

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_root(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome" in response.json()["message"]

def test_upload_files(client, mock_services):
    """Test the /upload endpoint."""
    # Mock the service function to return dummy chunks
    mock_process = mock_services["process"]
    mock_process.return_value = [MagicMock()]  # Return a list with one dummy chunk
    
    mock_new_retriever = mock_services["new_retriever"]

    # Create a dummy file
    dummy_file_content = b"This is a test pdf."
    dummy_file = ("test.pdf", io.BytesIO(dummy_file_content), "application/pdf")

    response = client.post("/api/v1/upload", files={"files": dummy_file})
    
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["message"] == "Successfully processed 1 chunks from 1 files."
    assert json_data["files_processed"] == ["test.pdf"]
    
    # Check that our service mocks were called
    mock_process.assert_called_once()
    mock_new_retriever.assert_called_once()

def test_upload_no_files(client):
    """Test /upload with no files, which is not allowed by FastAPI."""
    # The TestClient correctly simulates FastAPI's 422 for missing 'files'
    response = client.post("/api/v1/upload")
    assert response.status_code == 422 # Unprocessable Entity

def test_query_success(client, mock_services):
    """Test a successful /query request."""
    # Mock the graph invocation
    mock_graph = mock_services["graph"]
    mock_result = {
        "answer": "This is a test answer.",
        "sources": [{"filename": "test.pdf", "page": 1}]
    }
    mock_graph.invoke.return_value = mock_result
    
    # Mock get_retriever to "prove" docs are loaded
    mock_get_retriever = mock_services["get_retriever"]
    mock_get_retriever.return_value = MagicMock() # Return a dummy retriever

    response = client.post("/api/v1/query", json={"query": "What is this?"})
    
    assert response.status_code == 200
    json_data = response.json()
    
    # Validate with Pydantic model
    parsed_response = QueryResponse(**json_data)
    assert parsed_response.answer == "This is a test answer."
    assert len(parsed_response.sources) == 1
    assert parsed_response.sources[0] == Source(filename="test.pdf", page=1)
    
    # Check that graph was called with the correct input
    mock_graph.invoke.assert_called_once_with({"question": "What is this?"})
    mock_get_retriever.assert_called_once()

def test_query_no_docs_processed(client, mock_services):
    """Test /query when no documents have been uploaded."""
    # Mock get_retriever to raise the specific error
    mock_get_retriever = mock_services["get_retriever"]
    mock_get_retriever.side_effect = ValueError("No documents have been processed.")
    
    response = client.post("/api/v1/query", json={"query": "What is this?"})
    
    assert response.status_code == 400
    assert "No documents have been processed" in response.json()["detail"]
    mock_get_retriever.assert_called_once()

def test_query_graph_error(client, mock_services):
    """Test when the graph itself raises an internal error."""
    mock_graph = mock_services["graph"]
    mock_graph.invoke.side_effect = Exception("Graph failed")
    
    mock_get_retriever = mock_services["get_retriever"]
    mock_get_retriever.return_value = MagicMock()

    response = client.post("/api/v1/query", json={"query": "What is this?"})
    
    assert response.status_code == 500
    assert "An error occurred while generating the answer" in response.json()["detail"]