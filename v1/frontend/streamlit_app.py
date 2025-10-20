"""
Simple Streamlit UI to upload files and ask questions.
This frontend calls FastAPI endpoints defined above.
"""
import streamlit as st
import requests
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.title("Document QA — Upload & Ask")

st.header("1) Upload document")
uploaded_file = st.file_uploader("Choose a file (pdf, docx, txt, image)", type=["pdf","docx","txt","png","jpg","jpeg"])
if uploaded_file is not None:
    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
    resp = requests.post(f"{API_URL}/upload", files=files)
    if resp.ok:
        st.success(f"Uploaded: {uploaded_file.name}")
    else:
        st.error(f"Upload failed: {resp.text}")

st.header("2) Ask a question")
question = st.text_input("Enter your question about uploaded documents")
if st.button("Ask"):
    if not question.strip():
        st.warning("Write a question first")
    else:
        resp = requests.post(f"{API_URL}/ask", json={"question": question})
        if resp.ok:
            data = resp.json()
            st.subheader("Answer")
            st.write(data.get("answer"))
        else:
            st.error(f"Error: {resp.text}")
