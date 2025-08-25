# src/ai_assistant/plugins/rag_plugin.py
import os
import json
import tarfile
import tempfile
import fcntl
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from pathlib import Path
import structlog
import subprocess

from ..utils.git_utils import get_normalized_branch_name

try:
    import chromadb
    from chromadb.api.client import Client
except ImportError:
    chromadb = None
    Client = None

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SentenceTransformer = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False

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
        
        self.index_path = project_root / ai_settings.rag.local_index_path
        self.cache_path = project_root / ".ai_rag_cache"
        self.cache_path.mkdir(exist_ok=True)
        
        self.branch = get_normalized_branch_name(
            self.project_root,
            ai_settings.rag.default_branch
        ) if ai_settings.rag.enable_branch_awareness else "main"
        
        self._init_oracle_cloud()
        
        if self._should_download_index():
            self._download_latest_index()
        
        self.db_client = _get_chroma_client(ai_settings.rag, self.index_path)
            
        base_collection_name = ai_settings.rag.collection_name
        self.collection_name = f"{base_collection_name}_{self.branch}"
        
        logger.info("RAG plugin targeting collection", collection_name=self.collection_name)

        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.model_name = ai_settings.rag.embedding_model_name
                logger.info("Loading local embedding model", model_name=self.model_name)
                self.embedding_model = SentenceTransformer(self.model_name)
                logger.info("Local model loaded successfully.")
            except Exception as e:
                logger.error("Failed to load embedding model, RAG will be disabled.", error=str(e))
                self.embedding_model = None
        else:
            logger.warning("sentence-transformers is not installed. RAG queries disabled. Install with 'pip install -e .[client]'")
            self.embedding_model = None

    def _init_oracle_cloud(self):
        self.oci_config = ai_settings.rag.oracle_cloud
        self.oci_enabled = (
            self.oci_config and
            self.oci_config.enable_caching and
            self.oci_config.namespace and
            self.oci_config.bucket
        )

    def _should_download_index(self) -> bool:
        if not self.oci_enabled:
            return False
        
        metadata_path = self.cache_path / f"{self.branch}_metadata.json"
        if not metadata_path.exists():
            logger.info("No local cache metadata found. Will attempt to download index.")
            return True
            
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            last_checked = datetime.fromisoformat(metadata.get("last_checked_utc"))
            ttl = timedelta(hours=self.oci_config.cache_ttl_hours)
            
            if datetime.utcnow() - last_checked > ttl:
                logger.info("Cache TTL expired. Will check for a new index.")
                return True
            else:
                logger.info("Cache is up-to-date. Skipping download.")
                return False
        except (json.JSONDecodeError, KeyError, IOError) as e:
            logger.warning("Could not read cache metadata. Will attempt to download.", error=str(e))
            return True

    def _download_latest_index(self):
        logger.info("Attempting to download latest RAG index from OCI", branch=self.branch)
        lock_file_path = self.cache_path / f"{self.branch}.lock"
        
        with open(lock_file_path, "w") as lock_file:
            try:
                fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    archive_path = temp_path / "index.tar.gz"
                    object_name = f"indexes/{self.branch}/latest/index.tar.gz"
                    
                    command = [
                        "oci", "os", "object", "get",
                        "--namespace", self.oci_config.namespace,
                        "-bn", self.oci_config.bucket,
                        "--name", object_name,
                        "--file", str(archive_path)
                    ]
                    
                    logger.debug("Executing OCI command", command=" ".join(command))
                    result = subprocess.run(command, capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        logger.error("Failed to download index from OCI", stderr=result.stderr)
                        return

                    logger.info("Successfully downloaded index archive. Extracting...")
                    self.index_path.mkdir(exist_ok=True)
                    with tarfile.open(archive_path, "r:gz") as tar:
                        tar.extractall(path=self.index_path)
                    
                    logger.info("Index extracted successfully.", destination=str(self.index_path))
                    
                    # Update metadata on success
                    metadata = {"last_checked_utc": datetime.utcnow().isoformat()}
                    metadata_path = self.cache_path / f"{self.branch}_metadata.json"
                    with open(metadata_path, 'w') as f:
                        json.dump(metadata, f)

            except BlockingIOError:
                logger.warning("Another process is already downloading the index. Skipping.")
            except Exception as e:
                logger.error("An unexpected error occurred during index download.", error=str(e))
            finally:
                fcntl.flock(lock_file, fcntl.LOCK_UN)

    def _embed_query(self, query: str) -> List[float]:
        if not self.embedding_model: return []
        try:
            return self.embedding_model.encode([query])[0].tolist()
        except Exception as e:
            logger.error("Failed to embed query", error=str(e))
            return []
    
    def get_context(self, query: str, files: List[str]) -> Tuple[bool, str]:
        if not self.db_client or not self.embedding_model:
            return True, ""

        try:
            collection = self.db_client.get_collection(self.collection_name)
        except Exception:
            msg = f"RAG collection '{self.collection_name}' not found. Run 'ai-index' or check CI pipeline."
            logger.warning(msg)
            return True, "" # Not a fatal error, just no context

        enhanced_query = query
        if files:
            try:
                file_content = Path(files[0]).read_text(encoding='utf-8', errors='ignore')[:1000]
                enhanced_query = f"Based on this file content:\n{file_content}\n\nAnswer this query: {query}"
            except Exception as e:
                logger.warning("Could not read attached file for RAG enhancement", file=files[0], error=str(e))
                    
        try:
            query_embedding = self._embed_query(enhanced_query)
            if not query_embedding:
                return True, ""
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=5,
                include=["documents", "metadatas"]
            )
            
            if not results.get('documents') or not results['documents'][0]:
                return True, ""
            
            context_parts = ["# RAG-Retrieved Context\n"]
            for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                source = meta.get('source', 'unknown')
                context_parts.append(f"## Source: {source}\n```\n{doc}\n```\n")
            
            return True, "\n".join(context_parts)
        
        except Exception as e:
            error_msg = f"Error: Could not retrieve context from RAG system. Reason: {e}"
            logger.error("Error querying ChromaDB", error=str(e))
            return False, error_msg