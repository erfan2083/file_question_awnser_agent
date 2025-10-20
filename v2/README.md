# Local Hybrid RAG: Multi-Agent QA System

This is a full-stack, production-ready Document QA (Question-Answering) system. It uses a multi-agent graph (built with LangGraph) to orchestrate a hybrid retrieval pipeline (FAISS for semantic search and BM25 for lexical search).

The entire stack is designed to run locally and uses free, open-source models.

## Features

* **File Upload**: Supports `.pdf`, `.docx`, `.txt`, and images (`.png`, `.jpg`, `.jpeg`) with automatic OCR.
* **Hybrid Retrieval**: Combines `BM25` (keyword-based) and `FAISS` (semantic-based) retrieval for robust results.
* **Multi-Agent QA**: Uses LangGraph to define a graph of "agents" (nodes) for retrieval, relevance grading, and answer generation.
* **Citations**: Provides concise answers with citations (filename and page number).
* **Web Interface**: A clean React (Vite) frontend with file upload and a chat interface.
* **Dockerized**: Fully containerized with `docker-compose` for easy, one-command startup.

## Tech Stack

* **Backend**: FastAPI (Python)
* **Orchestration**: LangChain & LangGraph
* **LLM**: `microsoft/Phi-3-mini-4k-instruct` (A 3.8B parameter model, chosen as the best-in-class, CPU-friendly model matching the "3b" spec. It's loaded in 8-bit for low resource usage.)
* **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (Fast, high-quality local embeddings)
* **Vectorstore**: FAISS (CPU)
* **Lexical Search**: `rank_bm25`
* **Document Loading**: `unstructured`, `pypdf`, `pytesseract` (for OCR)
* **Frontend**: React (Vite)
* **Containerization**: Docker & Docker Compose

---

## How to Run (Docker - Recommended)

This is the simplest way to get the entire application running.

**Prerequisites:**
* [Docker](https://www.docker.com/products/docker-desktop/) installed and running.

**Steps:**

1.  **Clone the repository:**
    ```sh
    git clone <repository_url>
    cd local-hybrid-rag
    ```

2.  **Build and run the containers:**
    ```sh
    docker-compose up --build
    ```

3.  **Wait for the services to start:**
    * The `backend` service will download the LLM and embedding models on first run. This can take several minutes and a significant amount of disk space (~10-15GB).
    * You can monitor the logs by running `docker-compose logs -f backend`.

4.  **Access the application:**
    * **Frontend (Web UI)**: [http://localhost:5173](http://localhost:5173)
    * **Backend (API Docs)**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## How to Run (Local Development)

This method is for developers who want to run the services directly on their host machine.

### 1. Backend Setup

**Prerequisites:**
* Python 3.11+
* [Tesseract OCR Engine](https://tesseract-ocr.github.io/tessdoc/Installation.html):
    * **macOS**: `brew install tesseract poppler`
    * **Ubuntu/Debian**: `sudo apt-get update && sudo apt-get install -y tesseract-ocr poppler-utils`
    * **Windows**: Download the installer from the official Tesseract GitHub.

**Steps:**

1.  **Navigate to the backend directory:**
    ```sh
    cd backend
    ```

2.  **Create a virtual environment and activate it:**
    ```sh
    python3 -m venv venv
    source venv/bin/activate
    # On Windows: venv\Scripts\activate
    ```

3.  **Install Python dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

4.  **Run the backend server:**
    ```sh
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```
    The server will be running at `http://localhost:8000`.

### 2. Frontend Setup

**Prerequisites:**
* Node.js v18+ and npm

**Steps:**

1.  **Open a new terminal** and navigate to the frontend directory:
    ```sh
    cd frontend
    ```

2.  **Install Node modules:**
    ```sh
    npm install
    ```

3.  **Run the frontend development server:**
    ```sh
    npm run dev
    ```
    The server will be running at `http://localhost:5173`. The `vite.config.js` is pre-configured to proxy API requests to the backend at `http://localhost:8000`.

---

## Running Tests

You can validate the backend logic by running the included tests.

1.  **Navigate to the `backend` directory:**
    ```sh
    cd backend
    ```

2.  **Ensure your virtual environment is active** and dependencies are installed.

3.  **Run pytest:**
    ```sh
    pytest
    ```

---

## Project Structure

* `backend/`: FastAPI application.
    * `app/api/routes.py`: API endpoints for `/upload` and `/query`.
    * `app/core/config.py`: Centralized configuration (model names, paths).
    * `app/core/models.py`: Pydantic models for API requests/responses.
    * `app/services/ingestion.py`: Handles loading all file types (PDF, DOCX, TXT, OCR for images) and chunking.
    * `app/services/retrieval.py`: Manages the hybrid retriever. Handles creating, saving, and loading the FAISS index and rebuilding the BM25 retriever.
    * `app/services/graph.py`: The core logic. Defines the LangGraph multi-agent state and the nodes (agents) for:
        1.  `retrieve`: Runs the hybrid retriever.
        2.  `grade_documents`: Uses the LLM to check if retrieved docs are relevant.
        3.  `generate`: Generates an answer using the relevant docs (RAG).
        4.  `generate_no_docs`: Generates a fallback answer if no relevant docs are found.
        5.  `format_output`: Cleans the LLM output and formats citations.
* `frontend/`: React (Vite) application.
    * `src/components/FileUpload.jsx`: Component for uploading documents.
    * `src/components/ChatInterface.jsx`: Component for the chat UI, handling user queries and displaying bot responses with sources.
* `docker-compose.yml`: Orchestrates the `backend` and `frontend` services.
* `Dockerfile`: Container definitions for both services.