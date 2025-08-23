from typing import List
from pathlib import Path
import structlog

import chromadb
from sentence_transformers import SentenceTransformer

from ..context_plugin import ContextPluginBase
from ..config import ai_settings

logger = structlog.get_logger(__name__)

class RAGContextPlugin(ContextPluginBase):
    """Retrieval-Augmented Generation context plugin for AI Assistant."""
    name = "RAG Plugin"
    
    def __init__(self, project_root: Path):
        """Initializes the RAG plugin with ChromaDB client and embedding model."""
        super().__init__(project_root)
        
        # Initialize ChromaDB client
        self.index_path = project_root / ".ai_rag_index"
        self.db_client = chromadb.PersistentClient(path=str(self.index_path))
        self.collection_name = "codebase_collection"
        
        # Load embedding model from config
        self.model_name = ai_settings.rag.embedding_model_name
        logger.info("Loading local embedding model", model_name=self.model_name)
        self.embedding_model = SentenceTransformer(self.model_name)
        logger.info("Local model loaded successfully.")
        
    def _embed_query(self, query: str) -> List[float]:
        """Embed the user query using the sentence-transformers model."""
        try:
            embedding = self.embedding_model.encode([query])
            return embedding[0].tolist()
        except Exception as e:
            logger.error("Failed to embed query", error=str(e))
            return []
    
    def get_context(self, query: str, files: List[str]) -> str:
        """
        Retrieves relevant context from the vector database based on the user query.
        
        Args:
            query: The user's query string
            files: List of file paths (not used in RAG plugin)
            
        Returns:
            Formatted context string with source citations
        """
        # Embed the query
        query_embedding = self._embed_query(query)
        if not query_embedding:
            logger.warning("Failed to generate query embedding, returning empty context")
            return ""
        
        try:
            # Get the collection
            collection = self.db_client.get_collection(self.collection_name)
            
            # Query for top 5 most relevant results
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=5,
                include=["documents", "metadatas"]
            )
            
            if not results['documents'] or not results['documents'][0]:
                logger.info("No relevant documents found for query")
                return ""
            
            # Format the results with source citations
            context_parts = ["# RAG-Retrieved Context\n\n"]
            
            for i, (document, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                source_file = metadata.get('source', 'unknown')
                chunk_index = metadata.get('chunk_index', 0)
                
                context_parts.append(f"## Source: {source_file} (Chunk {chunk_index})\n")
                context_parts.append(f"```\n{document}\n```\n\n")
            
            return "".join(context_parts)
            
        except Exception as e:
            logger.error("Error querying ChromaDB", error=str(e))
            return ""

    def __del__(self):
        """Cleanup method to handle resource cleanup if needed."""
        try:
            if hasattr(self, 'embedding_model'):
                # SentenceTransformer models don't typically need explicit cleanup
                pass
        except Exception as e:
            logger.warning("Error during plugin cleanup", error=str(e))
