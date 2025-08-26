# src/ai_assistant/plugins/rag_plugin.py

from pathlib import Path
from typing import List, Tuple, Optional
import structlog

try:
    import chromadb
    from sentence_transformers import SentenceTransformer
except ImportError:
    chromadb = None
    SentenceTransformer = None

from ..config import ai_settings
from ..context_plugin import ContextPluginBase
from ..utils.git_utils import get_normalized_branch_name
from ..reranker import get_reranker, Reranker

logger = structlog.get_logger()

class ChromaDBClient:
    """A client to connect to and query a ChromaDB collection."""
    def __init__(self, project_root: Path):
        self.host = ai_settings.rag.chroma_server_host
        self.port = ai_settings.rag.chroma_server_port
        self.ssl = ai_settings.rag.chroma_server_ssl
        self.project_root = project_root
        self.client = None
        self.collection = None
        self.embed_model = None

    def connect(self) -> Tuple[bool, str]:
        if not chromadb:
            return (False, "ChromaDB is not installed. Please run 'pip install -e .[client]'")
        
        try:
            if self.host:
                logger.debug("Connecting to remote ChromaDB server", host=self.host, port=self.port)
                self.client = chromadb.HttpClient(host=self.host, port=self.port, ssl=self.ssl)
            else:
                self.local_path = self.project_root / ai_settings.rag.local_index_path
                if not self.local_path.exists():
                    return (False, f"Local index path does not exist: {self.local_path}. Please run the indexer.")
                logger.debug("Connecting to local ChromaDB", path=str(self.local_path))
                self.client = chromadb.PersistentClient(path=str(self.local_path))

            branch = get_normalized_branch_name(self.project_root, ai_settings.rag.default_branch)
            collection_name = f"{ai_settings.rag.collection_name}_{branch}"
            
            logger.debug("Getting collection", collection_name=collection_name)
            self.collection = self.client.get_collection(collection_name)
            
            logger.debug("Loading embedding model for queries", model=ai_settings.rag.embedding_model_name)
            self.embed_model = SentenceTransformer(ai_settings.rag.embedding_model_name)
            
            return (True, "Successfully connected to ChromaDB and loaded models.")
        except Exception as e:
            logger.error("ChromaDB connection failed", error=str(e))
            return (False, f"Failed to connect to ChromaDB or load models: {e}")

    def query(self, query_text: str, n_results: int) -> List[str]:
        if not self.collection or not self.embed_model:
            logger.error("Cannot query, ChromaDB client not connected.")
            return []
        try:
            embedding = self.embed_model.encode([query_text])[0].tolist()
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=n_results
            )
            return results['documents'][0] if results and 'documents' in results else []
        except Exception as e:
            logger.error("ChromaDB query failed", error=str(e))
            return []

class RAGContextPlugin(ContextPluginBase):
    name = "Codebase-Aware RAG"

    def __init__(self, project_root: Path):
        super().__init__(project_root)
        self.db_client = ChromaDBClient(project_root)
        self.is_connected, self.message = self.db_client.connect()
        # --- NEW ---
        self.reranker: Optional[Reranker] = None
        if ai_settings.rag.enable_reranking:
            logger.info("Reranking is enabled. Initializing reranker.")
            self.reranker = get_reranker()
        else:
            logger.info("Reranking is disabled.")

    def get_context(self, query: str, files: List[str]) -> Tuple[bool, str]:
        if not self.is_connected:
            return (False, self.message)

        # --- MODIFIED ---
        # Retrieve more documents initially to give the reranker a good selection.
        n_results = ai_settings.rag.retrieval_n_results
        logger.info("Retrieving documents from vector store...", query=query, n_results=n_results)
        documents = self.db_client.query(query, n_results=n_results)

        if not documents:
            return (True, "<Context>No relevant documents found in the codebase for the query.</Context>")

        final_documents = documents
        # --- NEW: Reranking Step ---
        if self.reranker:
            reranked_docs = self.reranker.rerank(query, documents)
            top_n = ai_settings.rag.rerank_top_n
            final_documents = reranked_docs[:top_n]
            logger.info("Reranked documents.", initial_count=len(documents), final_count=len(final_documents))

        context_str = "\n\n---\n\n".join(
            f"<ContextChunk source=\"{doc_source}\">\n{doc_content}\n</ContextChunk>"
            for doc_source, doc_content in self._extract_source(final_documents)
        )
        
        return (True, context_str)

    def _extract_source(self, documents: List[str]) -> List[Tuple[str, str]]:
        # This is a placeholder. In a real scenario, the source would be in the metadata.
        # For now, we'll assume the first line might be a source comment.
        results = []
        for doc in documents:
            # A simple heuristic to find a source path
            first_line = doc.split('\n')[0]
            if first_line.strip().startswith(('#', '//')) and '/' in first_line:
                source = first_line.strip('#/ ').strip()
                content = '\n'.join(doc.split('\n')[1:])
                results.append((source, content))
            else:
                # If no source found, use a placeholder
                results.append(("unknown", doc))
        return results