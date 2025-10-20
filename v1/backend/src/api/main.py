"""
FastAPI app exposing endpoints:
- POST /upload  -> upload file and index it
- POST /ask     -> ask a question (simple retrieval + answer)
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ingestion import save_upload_file, ingest_file
from pathlib import Path
from config import VECTORSTORE_PATH, OPENAI_API_KEY, LLM_MODEL
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from vectorstore import create_or_load_vectorstore
import uvicorn
import os

app = FastAPI(title="Document QA API")

# allow local dev origins (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    """
    Upload a document file. The endpoint saves the file and ingests it into FAISS.
    """
    try:
        dest = UPLOAD_DIR / file.filename
        save_upload_file(file, str(dest))
        ingest_file(str(dest), persist=True)
        return {"status": "success", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
async def ask(question: dict):
    """
    Ask endpoint expects JSON: {"question": "your question here"}
    It uses the FAISS index to retrieve relevant chunks and returns an answer.
    """
    q = question.get("question")
    if not q:
        raise HTTPException(status_code=400, detail="question field is required")

    # Ensure vectorstore exists
    if not VECTORSTORE_PATH.exists():
        raise HTTPException(status_code=400, detail="Vectorstore not found. Upload documents first.")

    # load vectorstore and build RetrievalQA
    embeddings = None  # handled internally by create_or_load_vectorstore
    db = create_or_load_vectorstore([], persist=True)  # load existing
    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 4})

    # LLM
    llm = ChatOpenAI(model_name=LLM_MODEL, openai_api_key=OPENAI_API_KEY, temperature=0.0)
    qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)

    answer = qa.run(q)
    # Note: answer may not include explicit citations yet — we'll add that later
    return {"question": q, "answer": answer}

if __name__ == "__main__":
    uvicorn.run("src.api.main:app", host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", "8000")), reload=True)
