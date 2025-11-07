"""Streamlit UI for Document QA System."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from loguru import logger

from src.agents.orchestrator import MultiAgentOrchestrator
from src.config.settings import settings
from src.document_processing import DocumentIndexer, chunk_document, load_document
from src.models.schemas import UtilityTask

# Page configuration
st.set_page_config(
    page_title="Document QA System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #424242;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #E3F2FD;
        border-left: 4px solid #1E88E5;
        margin: 1rem 0;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #E8F5E9;
        border-left: 4px solid #4CAF50;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""",
    unsafe_allow_html=True,
)


# Initialize session state
def init_session_state():
    """Initialize Streamlit session state."""
    if "orchestrator" not in st.session_state:
        st.session_state.orchestrator = MultiAgentOrchestrator()
        retriever_agent, _, _ = st.session_state.orchestrator.get_agents()
        st.session_state.indexer = (
            retriever_agent.get_retriever().get_retrievers()[0].get_indexer()
        )
        st.session_state.bm25_retriever = (
            retriever_agent.get_retriever().get_retrievers()[1]
        )

    if "documents" not in st.session_state:
        st.session_state.documents = []

    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []


init_session_state()


# Main UI
def main():
    """Main Streamlit application."""

    # Header
    st.markdown('<p class="main-header">📚 Document QA System</p>', unsafe_allow_html=True)
    st.markdown(
        "**Intelligent Document Question Answering with Multi-Agent Orchestration**"
    )

    # Sidebar
    with st.sidebar:
        st.markdown("### 🎛️ Control Panel")

        page = st.radio(
            "Navigate",
            [
                "📤 Upload Documents",
                "❓ Ask Questions",
                "🔧 Utility Tasks",
                "📊 System Info",
            ],
            label_visibility="collapsed",
        )

        st.markdown("---")

        st.markdown("### ⚙️ Settings")
        st.markdown(f"**Model:** {settings.llm_model}")
        st.markdown(f"**Chunk Size:** {settings.chunk_size}")
        st.markdown(f"**Top-K Results:** {settings.top_k_retrieval}")

        st.markdown("---")

        if st.button("🔄 Reset System"):
            if st.confirm("Are you sure? This will delete all documents."):
                st.session_state.indexer.reset_collection()
                st.session_state.bm25_retriever.clear()
                st.session_state.documents = []
                st.session_state.conversation_history = []
                st.success("System reset successfully!")

    # Main content based on page selection
    if page == "📤 Upload Documents":
        upload_documents_page()
    elif page == "❓ Ask Questions":
        ask_questions_page()
    elif page == "🔧 Utility Tasks":
        utility_tasks_page()
    elif page == "📊 System Info":
        system_info_page()


def upload_documents_page():
    """Document upload page."""
    st.markdown('<p class="sub-header">Upload Documents</p>', unsafe_allow_html=True)

    st.markdown(
        '<div class="info-box">📋 Supported formats: PDF, DOCX, TXT, Images (PNG, JPG)</div>',
        unsafe_allow_html=True,
    )

    uploaded_files = st.file_uploader(
        "Choose files",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        if st.button("📤 Upload and Index"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, uploaded_file in enumerate(uploaded_files):
                try:
                    status_text.text(f"Processing {uploaded_file.name}...")

                    # Read file content
                    contents = uploaded_file.read()

                    # Check file size
                    if len(contents) > settings.max_upload_size:
                        st.error(
                            f"❌ {uploaded_file.name} is too large (max {settings.max_upload_size / 1024 / 1024:.1f}MB)"
                        )
                        continue

                    # Load document
                    text, metadata = load_document(uploaded_file.name, contents)

                    # Chunk document
                    chunks = chunk_document(text, metadata)

                    # Index chunks
                    st.session_state.indexer.index_chunks(chunks, metadata)
                    st.session_state.bm25_retriever.index_chunks(chunks)

                    # Add to documents list
                    st.session_state.documents.append(
                        {
                            "id": metadata.document_id,
                            "name": metadata.filename,
                            "chunks": len(chunks),
                        }
                    )

                    st.success(
                        f"✅ {uploaded_file.name} uploaded and indexed ({len(chunks)} chunks)"
                    )

                except Exception as e:
                    st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
                    logger.error(f"Error processing file: {e}")

                progress_bar.progress((i + 1) / len(uploaded_files))

            status_text.text("✅ All files processed!")

    # Display uploaded documents
    if st.session_state.documents:
        st.markdown("---")
        st.markdown("### 📚 Uploaded Documents")

        for doc in st.session_state.documents:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{doc['name']}**")
            with col2:
                st.markdown(f"{doc['chunks']} chunks")
            with col3:
                if st.button("🗑️", key=f"delete_{doc['id']}"):
                    st.session_state.indexer.delete_document(doc['id'])
                    st.session_state.documents = [
                        d for d in st.session_state.documents if d["id"] != doc["id"]
                    ]
                    st.rerun()


def ask_questions_page():
    """Question answering page."""
    st.markdown('<p class="sub-header">Ask Questions</p>', unsafe_allow_html=True)

    if not st.session_state.documents:
        st.warning("⚠️ Please upload documents first!")
        return

    # Document filter
    doc_options = ["All Documents"] + [doc["name"] for doc in st.session_state.documents]
    selected_doc = st.selectbox("Filter by document:", doc_options)

    document_id = None
    if selected_doc != "All Documents":
        doc = next(d for d in st.session_state.documents if d["name"] == selected_doc)
        document_id = doc["id"]

    # Question input
    question = st.text_area(
        "Enter your question:",
        placeholder="What is the main topic of the document?",
        height=100,
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("🔍 Get Answer"):
            if question:
                with st.spinner("Thinking..."):
                    try:
                        answer = st.session_state.orchestrator.answer_question(
                            question=question, document_id=document_id
                        )

                        # Display answer
                        st.markdown("---")
                        st.markdown("### 💡 Answer")
                        st.markdown(
                            f'<div class="success-box">{answer.answer}</div>',
                            unsafe_allow_html=True,
                        )

                        # Display sources
                        if answer.sources:
                            st.markdown("### 📌 Sources")
                            for source in answer.sources[:3]:
                                st.markdown(f"- `{source}`")

                        # Add to conversation history
                        st.session_state.conversation_history.append(
                            {"question": question, "answer": answer.answer}
                        )

                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        logger.error(f"Error answering question: {e}")
            else:
                st.warning("⚠️ Please enter a question")

    with col2:
        clear_history = st.button("🗑️ Clear History")
        if clear_history:
            st.session_state.conversation_history = []
            st.rerun()

    # Display conversation history
    if st.session_state.conversation_history:
        st.markdown("---")
        st.markdown("### 💬 Conversation History")

        for i, conv in enumerate(reversed(st.session_state.conversation_history)):
            with st.expander(f"Q: {conv['question'][:50]}...", expanded=(i == 0)):
                st.markdown(f"**Question:** {conv['question']}")
                st.markdown(f"**Answer:** {conv['answer']}")


def utility_tasks_page():
    """Utility tasks page."""
    st.markdown('<p class="sub-header">Utility Tasks</p>', unsafe_allow_html=True)

    task = st.selectbox(
        "Select Task:",
        [
            "Translate",
            "Summarize",
            "Generate Checklist",
            "Extract Keywords",
        ],
    )

    input_method = st.radio("Input Method:", ["Enter Text", "Use Question"])

    if input_method == "Enter Text":
        text_input = st.text_area(
            "Enter text:",
            placeholder="Enter the text you want to process...",
            height=150,
        )

        if task == "Translate":
            target_lang = st.selectbox(
                "Target Language:",
                ["Spanish", "French", "German", "Arabic"],
            )
        else:
            target_lang = None

        if st.button("✨ Execute Task"):
            if text_input:
                with st.spinner("Processing..."):
                    try:
                        task_map = {
                            "Translate": UtilityTask.TRANSLATE,
                            "Summarize": UtilityTask.SUMMARIZE,
                            "Generate Checklist": UtilityTask.CHECKLIST,
                            "Extract Keywords": UtilityTask.EXTRACT_KEYWORDS,
                        }

                        result = st.session_state.orchestrator.perform_utility_task(
                            task=task_map[task],
                            text=text_input,
                            target_language=target_lang.lower() if target_lang else "es",
                        )

                        st.markdown("---")
                        st.markdown("### ✅ Result")
                        st.markdown(
                            f'<div class="success-box">{result}</div>',
                            unsafe_allow_html=True,
                        )

                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        logger.error(f"Error in utility task: {e}")
            else:
                st.warning("⚠️ Please enter text")

    else:
        question_input = st.text_input(
            "Enter question:",
            placeholder="What are the key points in the document?",
        )

        if st.button("✨ Execute Task"):
            if question_input:
                with st.spinner("Processing..."):
                    try:
                        task_map = {
                            "Summarize": UtilityTask.SUMMARIZE,
                            "Generate Checklist": UtilityTask.CHECKLIST,
                            "Extract Keywords": UtilityTask.EXTRACT_KEYWORDS,
                        }

                        if task == "Translate":
                            st.error("Translation requires direct text input")
                            return

                        result = st.session_state.orchestrator.perform_utility_task(
                            task=task_map[task], question=question_input
                        )

                        st.markdown("---")
                        st.markdown("### ✅ Result")
                        st.markdown(
                            f'<div class="success-box">{result}</div>',
                            unsafe_allow_html=True,
                        )

                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        logger.error(f"Error in utility task: {e}")
            else:
                st.warning("⚠️ Please enter a question")


def system_info_page():
    """System information page."""
    st.markdown('<p class="sub-header">System Information</p>', unsafe_allow_html=True)

    # Collection stats
    stats = st.session_state.indexer.get_collection_stats()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Documents", len(st.session_state.documents))

    with col2:
        st.metric("Total Chunks", stats.get("total_chunks", 0))

    with col3:
        st.metric("BM25 Corpus Size", st.session_state.bm25_retriever.get_corpus_size())

    # Configuration
    st.markdown("---")
    st.markdown("### ⚙️ Configuration")

    config_data = {
        "LLM Model": settings.llm_model,
        "Embedding Model": settings.embedding_model,
        "Chunk Size": settings.chunk_size,
        "Chunk Overlap": settings.chunk_overlap,
        "Top-K Retrieval": settings.top_k_retrieval,
        "Rerank Top-K": settings.rerank_top_k,
        "BM25 Weight": settings.bm25_weight,
        "Vector Weight": settings.vector_weight,
    }

    for key, value in config_data.items():
        st.markdown(f"**{key}:** `{value}`")


if __name__ == "__main__":
    # Configure logging
    logger.add(
        "logs/streamlit.log",
        rotation="500 MB",
        retention="10 days",
        level=settings.log_level,
    )

    main()
