# src/ai_assistant/plugins/rag_plugin.py
from typing import List, Optional
from pathlib import Path
import structlog
import subprocess

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

def _get_chroma_client(rag_config: ai_settings.rag, index_path: Path) -> Optional[Client]:
    if not chromadb:
        logger.warning("ChromaDB not installed. RAG features disabled. Install with 'pip install -e .[client]' or 'pip install -e .[indexing]'")
        return None

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
    
    # Local persistent mode (requires full chromadb)
    # Check for the specific class before trying to use it
    if hasattr(chromadb, 'PersistentClient'):
        logger.info("Using local persistent ChromaDB index", path=str(index_path))
        return chromadb.PersistentClient(path=str(index_path))
    else:
        logger.error("Local RAG index detected, but full 'chromadb' package is not installed. Please install with '-e .[indexing]' or configure a remote server.")
        return None

class RAGContextPlugin(ContextPluginBase):
    name = "RAG Plugin"
    
    def __init__(self, project_root: Path):
        super().__init__(project_root)
        
        self.index_path = project_root / ".ai_rag_index"
        self.db_client = _get_chroma_client(ai_settings.rag, self.index_path)
        
        # --- FIX: Correctly determine branch and collection name ---
        if ai_settings.rag.enable_branch_awareness:
            try:
                result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], capture_output=True, text=True, check=True, cwd=project_root)
                current_branch = result.stdout.strip().replace('/', '_')
            except Exception:
                logger.warning("Could not detect git branch, falling back to default.", default=ai_settings.rag.default_branch)
                current_branch = ai_settings.rag.default_branch
            
            base_collection_name = ai_settings.rag.collection_name
            self.collection_name = f"{base_collection_name}_{current_branch}"
        else:
            self.collection_name = ai_settings.rag.collection_name
        
        logger.info("RAG plugin targeting collection", collection_name=self.collection_name)

        try:
            self.model_name = ai_settings.rag.embedding_model_name
            self.embedding_model = SentenceTransformer(self.model_name)
        except Exception as e:
            logger.error("Failed to load embedding model, RAG will be disabled.", error=str(e))
            self.embedding_model = None
        
    def _embed_query(self, query: str) -> List[float]:
        if not self.embedding_model: return []
        try:
            return self.embedding_model.encode([query])[0].tolist()
        except Exception as e:
            logger.error("Failed to embed query", error=str(e))
            return []
    
    def get_context(self, query: str, files: List[str]) -> str:
        if not self.db_client or not self.embedding_model:
            return "" # Logged during init, no need to be noisy here.

        try:
            collection = self.db_client.get_collection(self.collection_name)
        except Exception:
            logger.warning(f"RAG collection '{self.collection_name}' not found. Run 'ai-index'.")
            return ""

        try:
            query_embedding = self._embed_query(query)
            if not query_embedding:
                return ""
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=5,
                include=["documents", "metadatas"]
            )
            
            if not results.get('documents') or not results['documents'][0]:
                return ""
            
            context_parts = ["# RAG-Retrieved Context\n"]
            for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                source = meta.get('source', 'unknown')
                context_parts.append(f"## Source: {source}\n```\n{doc}\n```\n")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error("Error querying ChromaDB", error=str(e))
            return f"Error: Could not retrieve context from RAG system. Reason: {e}"