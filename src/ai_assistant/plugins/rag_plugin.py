# src/ai_assistant/plugins/rag_plugin.py

import shutil
import tarfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Tuple, Optional
import structlog
import json

try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    import oci
except ImportError:
    chromadb = None
    SentenceTransformer = None
    oci = None

from ..config import ai_settings
from ..context_plugin import ContextPluginBase
from ..utils.git_utils import get_normalized_branch_name
from ..reranker import get_reranker, Reranker

logger = structlog.get_logger()

# --- HELPER FUNCTION TO MANAGE OCI CONNECTION ---
def _get_oci_client() -> Optional[oci.object_storage.ObjectStorageClient]:
    if not oci:
        return None
    try:
        # This will use the standard OCI config file (~/.oci/config)
        config = oci.config.from_file()
        return oci.object_storage.ObjectStorageClient(config)
    except oci.exceptions.ConfigFileNotFound:
        logger.error("OCI config file not found at ~/.oci/config. Cannot download index.")
        return None
    except Exception as e:
        logger.error("Failed to initialize OCI client", error=str(e))
        return None
    
class ChromaDBClient:
    """A client to connect to and query a LOCAL ChromaDB collection."""
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.client = None
        self.collection = None
        self.embed_model = None

    def connect(self) -> Tuple[bool, str]:
        if not chromadb:
            return (False, "ChromaDB is not installed. Please run 'pip install -e .[client]'")
        
        try:
            # --- SIMPLIFIED: NO MORE REMOTE HOST OPTION ---
            self.local_path = self.project_root / ai_settings.rag.local_index_path
            if not self.local_path.exists():
                # This case should be caught by the sync logic, but it's a good safeguard.
                return (False, f"Local index path does not exist: {self.local_path}.")
            
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

    def query(self, query_text: str, n_results: int) -> dict:
        if not self.collection or not self.embed_model:
            logger.error("Cannot query, ChromaDB client not connected.")
            return {}
        try:
            embedding = self.embed_model.encode([query_text])[0].tolist()
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=n_results,
                include=["metadatas", "documents"]  # <-- KEY CHANGE: Request metadata
            )
            return results if results else {}
        except Exception as e:
            logger.error("ChromaDB query failed", error=str(e))
            return {}

class RAGContextPlugin(ContextPluginBase):
    name = "Codebase-Aware RAG"

    def __init__(self, project_root: Path):
        super().__init__(project_root)
        self.local_index_path = self.project_root / ai_settings.rag.local_index_path
        self.cache_state_path = self.local_index_path / ".cache_state.json"
        
        # --- NEW CORE LOGIC ---
        # This function now handles everything: checking TTL, downloading, and unpacking.
        self.is_ready, self.message = self._ensure_local_index_is_fresh()
        
        self.db_client = None
        self.reranker = None

        if self.is_ready:
            self.db_client = ChromaDBClient(project_root)
            self.is_connected, self.message = self.db_client.connect()
            if ai_settings.rag.enable_reranking:
                logger.info("Reranking is enabled. Initializing reranker.")
                self.reranker = get_reranker()
        else:
            self.is_connected = False
            # The error message from _ensure_local_index_is_fresh will be used.


    def _ensure_local_index_is_fresh(self) -> Tuple[bool, str]:
        """The new heart of the plugin. Manages the cache lifecycle."""
        cfg = ai_settings.rag.oracle_cloud
        if not cfg or not cfg.enable_caching:
            return (True, "Local index caching is disabled.")

        # Check if the cache is stale
        if self.cache_state_path.exists():
            try:
                state = json.loads(self.cache_state_path.read_text())
                last_sync_dt = datetime.fromisoformat(state.get("last_synced_utc"))
                ttl = timedelta(hours=cfg.cache_ttl_hours)
                if datetime.now(timezone.utc) < last_sync_dt + ttl:
                    logger.info("Local RAG index is fresh. Using cache.", last_sync=last_sync_dt.isoformat())
                    return (True, "Cache is fresh.")
            except Exception as e:
                logger.warning("Could not read cache state file. Forcing re-download.", error=str(e))

        logger.info("Local RAG index is stale or missing. Syncing from OCI Object Storage...")
        
        # --- OCI DOWNLOAD AND UNPACK LOGIC ---
        oci_client = _get_oci_client()
        if not oci_client:
            return (False, "OCI client could not be initialized. Check your ~/.oci/config.")

        branch = get_normalized_branch_name(self.project_root, ai_settings.rag.default_branch)
        object_name = f"indexes/{branch}/latest/index.tar.gz"
        download_path = self.local_index_path.with_suffix('.tar.gz.download')

        try:
            # 1. Download the file
            logger.info("Downloading index...", bucket=cfg.bucket, object=object_name)
            get_obj = oci_client.get_object(cfg.namespace, cfg.bucket, object_name)
            
            download_path.parent.mkdir(exist_ok=True)
            with open(download_path, 'wb') as f:
                for chunk in get_obj.data.raw.stream(1024 * 1024, decode_content=False):
                    f.write(chunk)

            # 2. Clean up old index and unpack new one
            if self.local_index_path.exists():
                shutil.rmtree(self.local_index_path)
            self.local_index_path.mkdir()

            logger.info("Unpacking index...", source=download_path, dest=self.local_index_path)
            with tarfile.open(download_path, "r:gz") as tar:
                tar.extractall(path=self.local_index_path)

            # 3. Update cache state file
            new_state = {"last_synced_utc": datetime.now(timezone.utc).isoformat(), "branch": branch}
            self.cache_state_path.write_text(json.dumps(new_state, indent=2))
            
            logger.info("Successfully synced and unpacked RAG index from OCI.")
            return (True, "Index synced from OCI.")

        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                msg = f"Index not found in OCI for branch '{branch}'. Please run the indexing CI/CD job."
                logger.error(msg, bucket=cfg.bucket, object=object_name)
                return (False, msg)
            logger.error("OCI Service Error during download", error=str(e))
            return (False, f"OCI Service Error: {e.message}")
        except Exception as e:
            logger.error("Failed during index sync process", error=str(e))
            return (False, f"An unexpected error occurred during sync: {e}")
        finally:
            # 4. Clean up downloaded tarball
            if download_path.exists():
                download_path.unlink()

    def get_context(self, query: str, files: List[str]) -> Tuple[bool, str]:
        if not self.is_ready or not self.is_connected:
            return (False, self.message)

        n_results = ai_settings.rag.retrieval_n_results
        logger.info("Retrieving documents from vector store...", query=query, n_results=n_results)
        
        results = self.db_client.query(query, n_results=n_results)

        if not results or not results.get('documents') or not results['documents'][0]:
            return (True, "<Context>No relevant documents found in the codebase for the query.</Context>")

        initial_docs = results['documents'][0]
        initial_metas = results.get('metadatas', [[]])[0] # Safely get metadatas
        
        # --- Defensive metadata handling ---
        doc_to_meta_map = {}
        if initial_metas and len(initial_metas) == len(initial_docs):
            doc_to_meta_map = {doc: meta for doc, meta in zip(initial_docs, initial_metas)}
        else:
            logger.warning(
                "Metadata unavailable or mismatched with documents. Using fallback.",
                doc_count=len(initial_docs),
                meta_count=len(initial_metas)
            )
            # Fallback: create minimal metadata to prevent crashes
            for i, doc in enumerate(initial_docs):
                doc_to_meta_map[doc] = {"source": f"unknown_source_{i+1}", "chunk_index": i}
        
        final_documents = initial_docs
        if self.reranker:
            reranked_docs = self.reranker.rerank(query, initial_docs)
            top_n = ai_settings.rag.rerank_top_n
            final_documents = reranked_docs[:top_n]
            logger.info("Reranked documents.", initial_count=len(initial_docs), final_count=len(final_documents))

        context_str = "\n\n---\n\n".join(
            f"<ContextChunk source=\"{doc_to_meta_map.get(doc, {}).get('source', 'unknown')}\">\n{doc}\n</ContextChunk>"
            for doc in final_documents
        )
        
        return (True, context_str)
