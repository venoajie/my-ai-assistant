# src\ai_assistant\plugins\rag_plugin.py
from typing import List, Optional
from pathlib import Path
import structlog

# ### --- FIX: Conditionally import chromadb --- ###
try:
    import chromadb
    from chromadb.api.client import Client
except ImportError:
    chromadb = None
    Client = None

from sentence_transformers import SentenceTransformer

from ..context_plugin import ContextPluginBase
from ..config import ai_settings

logger = structlog.get_logger(__name__)

# ### --- FIX: Create a client factory function --- ###
def _get_chroma_client(rag_config: ai_settings.rag, index_path: Path) -> Optional[Client]:
    """
    Gets the appropriate ChromaDB client based on configuration.
    Returns None if RAG is not configured or dependencies are missing.
    """
    if not chromadb:
        logger.warning("ChromaDB not installed. RAG features disabled. Install with 'pip install -e .[client]' or 'pip install -e .[indexing]'")
        return None

    # Client-server mode
    if rag_config.chroma_server_host and rag_config.chroma_server_port:
        logger.info("Connecting to remote ChromaDB server", host=rag_config.chroma_server_host, port=rag_config.chroma_server_port)
        try:
            return chromadb.HttpClient(
                host=rag_config.chroma_server_host,
                port=rag_config.chroma_server_port,
                ssl=rag_config.chroma_server_ssl,
            )
        except Exception as e:
            logger.error("Failed to connect to ChromaDB server", error=str(e))
            return None
    
    # Local persistent mode
    logger.info("Using local persistent ChromaDB index", path=str(index_path))
    return chromadb.PersistentClient(path=str(index_path))


class RAGContextPlugin(ContextPluginBase):
    """Retrieval-Augmented Generation context plugin for AI Assistant."""
    name = "RAG Plugin"
    
    def __init__(self, project_root: Path):
        """Initializes the RAG plugin with ChromaDB client and embedding model."""
        super().__init__(project_root)
        
        self.index_path = project_root / ".ai_rag_index"
        self.db_client = _get_chroma_client(ai_settings.rag, self.index_path)
        self.collection_name = ai_settings.rag.collection_name
        
        # Embedding model is only needed for querying, which happens on the client.
        # However, it's a heavy dependency. We assume if RAG is used, it's installed.
        try:
            self.model_name = ai_settings.rag.embedding_model_name
            logger.info("Loading local embedding model", model_name=self.model_name)
            self.embedding_model = SentenceTransformer(self.model_name)
            logger.info("Local model loaded successfully.")
        except ImportError:
            logger.error("sentence-transformers is not installed. Cannot perform RAG queries. Install with 'pip install -e .[indexing]'")
            self.embedding_model = None
        except Exception as e:
            logger.error("Failed to load embedding model", error=str(e))
            self.embedding_model = None
        
    def _embed_query(self, query: str) -> List[float]:
        """Embed the user query using the sentence-transformers model."""
        if not self.embedding_model:
            return []
        try:
            embedding = self.embedding_model.encode([query])
            return embedding[0].tolist()
        except Exception as e:
            logger.error("Failed to embed query", error=str(e))
            return []
    
    def get_context(self, query: str, files: List[str]) -> str:
        """
        Retrieves relevant context from the vector database based on the user query.
        """
        # ### --- FIX: Handle cases where client or model failed to initialize --- ###
        if not self.db_client:
            return "RAG system is not available (ChromaDB client could not be initialized)."
        if not self.embedding_model:
            return "RAG system is not available (Embedding model could not be loaded)."

        try:
            # Check if the collection exists before trying to get it.
            existing_collections = self.db_client.list_collections()
            if self.collection_name not in [c.name for c in existing_collections]:
                logger.warning(f"RAG collection '{self.collection_name}' not found. Run 'ai-index' on the server. Returning empty context.")
                return ""
            
            collection = self.db_client.get_collection(self.collection_name)

            query_embedding = self._embed_query(query)
            if not query_embedding:
                logger.warning("Failed to generate query embedding, returning empty context")
                return ""
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=5,
                include=["documents", "metadatas"]
            )
            
            if not results['documents'] or not results['documents'][0]:
                logger.info("No relevant documents found for query")
                return ""
            
            context_parts = ["# RAG-Retrieved Context\n\n"]
            for i, (document, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                source_file = metadata.get('source', 'unknown')
                chunk_index = metadata.get('chunk_index', 0)
                context_parts.append(f"## Source: {source_file} (Chunk {chunk_index})\n")
                context_parts.append(f"```\n{document}\n```\n\n")
            
            return "".join(context_parts)
            
        except Exception as e:
            logger.error("Error querying ChromaDB", error=str(e))
            return f"Error: Could not retrieve context from RAG system. Reason: {e}"

    def __del__(self):
        """Cleanup method to handle resource cleanup if needed."""
        try:
            if hasattr(self, 'embedding_model'):
                pass
        except Exception as e:
            logger.warning("Error during plugin cleanup", error=str(e))