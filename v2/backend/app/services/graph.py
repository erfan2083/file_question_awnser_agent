import logging
from typing import List, TypedDict, Annotated
import operator
import torch

from langchain.schema.document import Document
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_huggingface import HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline, BitsAndBytesConfig

from langgraph.graph import StateGraph, END

from app.core.config import settings
from app.services.retrieval import get_retriever

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- LLM Initialization ---

def get_llm():
    """
    Initializes and returns the local LLM pipeline.
    Uses 8-bit quantization for CPU-friendliness.
    """
    logger.info(f"Initializing LLM: {settings.LLM_MODEL_NAME}")
    
    # Quantization config for 8-bit loading
    quantization_config = BitsAndBytesConfig(load_in_8bit=True)
    
    device_map = "cuda" if torch.cuda.is_available() else "auto"
    logger.info(f"Loading LLM on device_map: {device_map}")

    try:
        tokenizer = AutoTokenizer.from_pretrained(settings.LLM_MODEL_NAME)
        model = AutoModelForCausalLM.from_pretrained(
            settings.LLM_MODEL_NAME,
            quantization_config=quantization_config,
            torch_dtype=torch.float16, # Use float16 for mixed precision
            device_map=device_map,
            trust_remote_code=True # Required for Phi-3
        )
        
        # Set pad_token_id to eos_token_id if it's not set
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token_id = tokenizer.eos_token_id

        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=512,
            temperature=0.1,
            top_p=0.95,
        )
        
        llm = HuggingFacePipeline(pipeline=pipe)
        logger.info("LLM Pipeline initialized successfully.")
        return llm
    except Exception as e:
        logger.error(f"Error initializing LLM: {e}", exc_info=True)
        # This is a critical failure
        raise

# Singleton LLM instance
llm = get_llm()

# --- Graph State ---

class GraphState(TypedDict):
    """
    Defines the state that is passed between nodes in the graph.
    """
    question: str
    documents: List[Document]
    generation: str
    answer: str
    sources: List[dict]


# --- Graph Nodes (Agents) ---

def retrieve_node(state: GraphState) -> GraphState:
    """
    Retrieval agent: Fetches documents from the hybrid retriever.
    """
    logger.info("Graph node: retrieve_node")
    question = state['question']
    retriever = get_retriever()
    documents = retriever.invoke(question)
    
    # De-duplicate documents based on page_content
    unique_docs = {doc.page_content: doc for doc in documents}.values()
    
    return {"documents": list(unique_docs)}

def grade_documents_node(state: GraphState) -> GraphState:
    """
    Grader agent: Uses the LLM to check if documents are relevant to the question.
    """
    logger.info("Graph node: grade_documents_node")
    question = state['question']
    documents = state['documents']
    
    if not documents:
        logger.warning("Grader: No documents to grade.")
        return {"documents": []}

    prompt = PromptTemplate(
        template="""<|system|>
You are a document grader. Your purpose is to determine if a document chunk is relevant to a user's question.
Respond with only 'yes' or 'no'.<|end|>
<|user|>
Question: {question}
Document:
{document}
<|end|>
<|assistant|>
""",
        input_variables=["question", "document"],
    )
    
    grader_chain = prompt | llm | StrOutputParser()
    
    filtered_docs = []
    for doc in documents:
        try:
            response = grader_chain.invoke({
                "question": question,
                "document": doc.page_content
            })
            # Clean response
            answer = response.strip().lower()
            if "yes" in answer:
                logger.info(f"Grader: Doc '{doc.metadata.get('source')}' is RELEVANT.")
                filtered_docs.append(doc)
            else:
                 logger.info(f"Grader: Doc '{doc.metadata.get('source')}' is NOT relevant.")
        except Exception as e:
            logger.error(f"Grader: Error grading doc: {e}")
            
    return {"documents": filtered_docs}

def generate_node(state: GraphState) -> GraphState:
    """
    Generator agent: Generates an answer using the RAG prompt.
    """
    logger.info("Graph node: generate_node")
    question = state['question']
    documents = state['documents']
    
    context = "\n\n---\n\n".join([doc.page_content for doc in documents])
    
    prompt = PromptTemplate(
        template="""<|system|>
You are a helpful Q&A assistant. Your task is to answer the user's question based *only* on the provided context.
- Be concise and direct.
- Do not use any information outside of the context.
- If the answer is not in the context, state that you cannot answer the question based on the provided documents.
- Do not mention the context in your answer (e.g., "Based on the context...").
<|end|>
<|user|>
Context:
{context}

Question:
{question}
<|end|>
<|assistant|>
""",
        input_variables=["context", "question"],
    )
    
    rag_chain = prompt | llm | StrOutputParser()
    
    generation = rag_chain.invoke({"context": context, "question": question})
    return {"generation": generation, "documents": documents}

def generate_no_docs_node(state: GraphState) -> GraphState:
    """
    Fallback agent: Generates a response when no relevant documents are found.
    """
    logger.info("Graph node: generate_no_docs_node")
    generation = "I'm sorry, but I couldn't find any relevant information in the uploaded documents to answer your question."
    return {"generation": generation, "documents": []}

def format_output_node(state: GraphState) -> GraphState:
    """
    Formatter agent: Cleans the LLM output and formats the citations.
    """
    logger.info("Graph node: format_output_node")
    generation = state['generation']
    documents = state['documents']
    
    # Basic cleaning of the generation
    # Phi-3 can sometimes include the prompt turn
    if "<|assistant|>" in generation:
        generation = generation.split("<|assistant|>")[-1].strip()
    
    # Create unique sources based on filename and page number
    source_map = {}
    for doc in documents:
        meta = doc.metadata
        filename = meta.get('source', 'Unknown')
        page = meta.get('page', None)
        
        # Create a unique key for filename-page combo
        key = (filename, page)
        if key not in source_map:
            source_map[key] = {"filename": filename, "page": page}
            
    sources = list(source_map.values())
    
    return {"answer": generation, "sources": sources}


# --- Graph Edges (Conditional Logic) ---

def grade_check_edge(state: GraphState) -> str:
    """
    Conditional edge: Decides whether to generate an answer or use the fallback.
    """
    logger.info("Graph edge: grade_check_edge")
    if state['documents']:
        logger.info("Decision: Relevant documents found. Proceeding to generate.")
        return "docs_found"
    else:
        logger.info("Decision: No relevant documents. Proceeding to fallback.")
        return "no_docs"


# --- Graph Assembly ---

def create_qa_graph() -> StateGraph:
    """
    Builds and compiles the complete LangGraph.
    """
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("grade_documents", grade_documents_node)
    workflow.add_node("generate", generate_node)
    workflow.add_node("generate_no_docs", generate_no_docs_node)
    workflow.add_node("format_output", format_output_node)

    # Define the flow
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "grade_documents")
    workflow.add_conditional_edges(
        "grade_documents",
        grade_check_edge,
        {
            "docs_found": "generate",
            "no_docs": "generate_no_docs"
        }
    )
    workflow.add_edge("generate", "format_output")
    workflow.add_edge("generate_no_docs", "format_output")
    workflow.add_edge("format_output", END)

    # Compile the graph
    app = workflow.compile()
    logger.info("LangGraph QA graph compiled successfully.")
    return app