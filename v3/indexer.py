"""Document indexing with vector embeddings."""

from typing import List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from loguru import logger

from src.config.settings import settings
from src.models.schemas import DocumentChunk, DocumentMetadata


class DocumentIndexer:
    """Indexes documents into vector store."""

    def __init__(self):
        """Initialize document indexer."""
        # Initialize ChromaDB client
        self.client = chromadb.Client(
            ChromaSettings(
                persist_directory=settings.chroma_persist_directory,
                anonymized_telemetry=False,
            )
        )

        # Initialize embeddings
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.embedding_model,
            google_api_key=settings.google_api_key,
        )

        # Get or create collection
        self.collection_name = settings.chroma_collection_name
        self.collection = self._get_or_create_collection()

        logger.info(
            f"Initialized DocumentIndexer with collection: {self.collection_name}"
        )

    def _get_or_create_collection(self):
        """Get existing collection or create new one."""
        try:
            collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Retrieved existing collection: {self.collection_name}")
        except Exception:
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"Created new collection: {self.collection_name}")

        return collection

    def index_chunks(
        self, chunks: List[DocumentChunk], metadata: DocumentMetadata
    ) -> None:
        """
        Index document chunks into vector store.

        Args:
            chunks: List of document chunks
            metadata: Document metadata
        """
        if not chunks:
            logger.warning(
                f"No chunks provided for indexing document {metadata.document_id}"
            )
            return

        # Prepare data for indexing
        texts = [chunk.text for chunk in chunks]
        chunk_ids = [chunk.chunk_id for chunk in chunks]

        # Generate embeddings
        logger.info(f"Generating embeddings for {len(chunks)} chunks...")
        embeddings = self.embeddings.embed_documents(texts)

        # Prepare metadata for each chunk
        metadatas = []
        for chunk in chunks:
            chunk_metadata = {
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "document_filename": metadata.filename,
                "document_format": metadata.format.value,
                "language": metadata.language,
            }
            chunk_metadata.update(chunk.metadata)
            metadatas.append(chunk_metadata)

        # Add to collection
        self.collection.add(
            ids=chunk_ids, embeddings=embeddings, documents=texts, metadatas=metadatas
        )

        logger.info(
            f"Indexed {len(chunks)} chunks for document {metadata.document_id}"
        )

        # Update metadata with chunk count
        metadata.num_chunks = len(chunks)

    def query(
        self,
        query_text: str,
        top_k: int = None,
        document_id: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> List[dict]:
        """
        Query the vector store.

        Args:
            query_text: Query text
            top_k: Number of results to return
            document_id: Optional document ID to filter by
            filters: Optional additional filters

        Returns:
            List of query results
        """
        top_k = top_k or settings.top_k_retrieval

        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query_text)

        # Prepare where clause for filtering
        where_clause = {}
        if document_id:
            where_clause["document_id"] = document_id
        if filters:
            where_clause.update(filters)

        # Query collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause if where_clause else None,
        )

        # Format results
        formatted_results = []
        if results["ids"] and len(results["ids"]) > 0:
            for i in range(len(results["ids"][0])):
                formatted_results.append(
                    {
                        "chunk_id": results["ids"][0][i],
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i],
                    }
                )

        logger.info(f"Query returned {len(formatted_results)} results")

        return formatted_results

    def delete_document(self, document_id: str) -> None:
        """
        Delete all chunks for a document.

        Args:
            document_id: Document ID to delete
        """
        # Get all chunks for this document
        results = self.collection.get(where={"document_id": document_id})

        if results["ids"]:
            # Delete chunks
            self.collection.delete(ids=results["ids"])
            logger.info(
                f"Deleted {len(results['ids'])} chunks for document {document_id}"
            )
        else:
            logger.warning(f"No chunks found for document {document_id}")

    def get_collection_stats(self) -> dict:
        """
        Get statistics about the collection.

        Returns:
            Dictionary with collection statistics
        """
        count = self.collection.count()
        return {
            "collection_name": self.collection_name,
            "total_chunks": count,
            "persist_directory": settings.chroma_persist_directory,
        }

    def reset_collection(self) -> None:
        """Reset (delete and recreate) the collection."""
        try:
            self.client.delete_collection(name=self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            logger.warning(f"Error deleting collection: {e}")

        self.collection = self._get_or_create_collection()
        logger.info(f"Reset collection: {self.collection_name}")
