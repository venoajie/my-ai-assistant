# src/ai_assistant/indexer.py

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator
import fnmatch
import subprocess
from datetime import datetime, timezone

try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    from openai import OpenAI
except ImportError:
    chromadb = None
    SentenceTransformer = None
    OpenAI = None

import structlog
from dotenv import load_dotenv

from .config import ai_settings
from .logging_config import setup_logging
from .utils.git_utils import get_normalized_branch_name

load_dotenv()
logger = structlog.get_logger()

EMBEDDING_BATCH_SIZE = 16
DEFAULT_IGNORE_PATTERNS = [".git/", ".venv/", "venv/", "__pycache__/", "*.pyc", "*.log", ".DS_Store", "node_modules/", "build/", "dist/", ".idea/", ".vscode/", "*.egg-info/", "src/ai_assistant/personas/", ".ai/personas/", "src/ai_assistant/internal_data/"]

# --- FIX 1: FULLY REFACTORED EmbeddingProvider CLASS ---
class EmbeddingProvider:
    def __init__(self, provider_name: str = "local"):
        self.provider_name = provider_name
        
        if self.provider_name == "local":
            self.model_name = ai_settings.rag.embedding_model_name
            logger.info("Loading local embedding model", model_name=self.model_name)
            if not SentenceTransformer:
                raise ImportError("sentence-transformers is not installed. Please run 'pip install -e .[indexing]'")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Local model loaded successfully.")
        elif self.provider_name == "openai":
            if not OpenAI:
                raise ImportError("openai library is not installed. Please run 'pip install openai'.")
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set.")
            self.client = OpenAI(api_key=api_key)
            self.model_name = "text-embedding-3-large" # Using the high-quality model
            logger.info("Using OpenAI embedding provider", model_name=self.model_name)
        else:
            raise ValueError(f"Unsupported embedding provider: {provider_name}")

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts: return []
        
        if self.provider_name == "local":
            try:
                embeddings = self.model.encode(texts, show_progress_bar=True)
                return [emb.tolist() for emb in embeddings]
            except Exception as e:
                logger.error("Failed to get local embeddings", error=str(e))
                return []
        elif self.provider_name == "openai":
            try:
                response = self.client.embeddings.create(input=texts, model=self.model_name)
                return [item.embedding for item in response.data]
            except Exception as e:
                logger.error("Failed to get OpenAI embeddings", error=str(e))
                return []
        return []

class Indexer:
    def __init__(self, project_root: Path, branch_override: Optional[str] = None, embedding_provider: str = "local"):
        self.project_root = project_root
        self.index_path = project_root / ai_settings.rag.local_index_path
        self.state_path = self.index_path / "state.json"
        self.index_path.mkdir(exist_ok=True)
        self.embedding_provider_name = embedding_provider

        if not chromadb:
            raise ImportError("ChromaDB is not installed. Please install with 'pip install -e .[indexing]'")
        
        if ai_settings.rag.chroma_server_host:
            raise ConnectionError("Indexer is configured to connect to a remote server, which is not allowed.")

        self.branch = branch_override or get_normalized_branch_name(self.project_root, ai_settings.rag.default_branch)
        
        base_collection_name = ai_settings.rag.collection_name
        self.collection_name = f"{base_collection_name}_{self.branch}"
        logger.info("Indexer targeting collection", collection_name=self.collection_name)
        
        self.db_client = chromadb.PersistentClient(path=str(self.index_path))
        self.collection = self.db_client.get_or_create_collection(self.collection_name)
        
        # --- FIX 2: PASS THE PROVIDER NAME TO THE CLASS ---
        self.embed_provider = EmbeddingProvider(provider_name=self.embedding_provider_name)
        
        self.state = self._load_state()
        self.ignore_patterns = self._load_ignore_patterns()

    # ... (all other methods like _load_state, _walk_project, etc., are unchanged) ...
    def _load_state(self) -> Dict[str, str]:
        if self.state_path.exists():
            with open(self.state_path, 'r') as f: return json.load(f)
        return {}

    def _save_state(self):
        temp_path = self.state_path.with_suffix('.tmp')
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2)
            temp_path.replace(self.state_path)
        except IOError as e:
            logger.error("Failed to save state atomically", error=str(e))
            if temp_path.exists():
                temp_path.unlink()

    def _load_ignore_patterns(self) -> List[str]:
        patterns = DEFAULT_IGNORE_PATTERNS
        patterns.append(str(self.index_path.relative_to(self.project_root)) + "/*")
        ignore_file = self.project_root / ".aiignore"
        if ignore_file.exists():
            with open(ignore_file, 'r') as f:
                patterns.extend([line.strip() for line in f if line.strip() and not line.startswith('#')])
        logger.info("Loaded ignore patterns", count=len(patterns))
        return patterns

    def _is_ignored(self, path: Path) -> bool:
        rel_path_str = os.path.normpath(str(path.relative_to(self.project_root)))
        for pattern in self.ignore_patterns:
            norm_pattern = os.path.normpath(pattern)
            if norm_pattern.endswith(os.sep):
                if (rel_path_str + os.sep).startswith(norm_pattern): return True
            elif fnmatch.fnmatch(rel_path_str, norm_pattern): return True
        return False

    def _walk_project(self) -> Generator[Path, None, None]:
        for root, dirs, files in os.walk(self.project_root, topdown=True):
            root_path = Path(root)
            dirs[:] = [d for d in dirs if not self._is_ignored(root_path / d)]
            for name in files:
                file_path = root_path / name
                if not self._is_ignored(file_path): yield file_path

    @staticmethod
    def _calculate_hash(file_path: Path) -> str:
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while buf := f.read(65536): hasher.update(buf)
        return hasher.hexdigest()

    @staticmethod
    def _is_chunk_valid(chunk: str, min_length: int = 20) -> bool:
        if len(chunk.strip()) < min_length: return False
        if len(chunk.strip()) / len(chunk) < 0.5: return False
        if chunk.count('\x00') > 0 or chunk.count('\ufffd') > 0: return False
        return True

    def _chunk_text(self, text: str, file_path: Path) -> List[str]:
        file_ext = file_path.suffix.lower()
        if file_ext == '.py':
            chunks = re.split(r'(^\s*class\s|^\s*def\s)', text, flags=re.MULTILINE)
            combined_chunks = [chunks[i] + chunks[i+1] for i in range(1, len(chunks), 2)]
            return combined_chunks if combined_chunks else [text]
        if file_ext == '.md':
            chunks = re.split(r'(^#+\s)', text, flags=re.MULTILINE)
            combined_chunks = [chunks[i] + chunks[i+1] for i in range(1, len(chunks), 2)]
            return combined_chunks if combined_chunks else [text]
        chunk_size, overlap = 1000, 200
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size - overlap)]

    def run(self, force_reindex: bool = False):
        logger.info("Starting indexer for project", project_root=self.project_root, provider=self.embedding_provider_name)
        if force_reindex:
            logger.warning("Forcing re-index of all files and clearing collection.")
            self.state = {}
            self.db_client.delete_collection(name=self.collection_name)
            self.collection = self.db_client.get_or_create_collection(self.collection_name)

        current_files = {str(p.relative_to(self.project_root)): p for p in self._walk_project()}
        
        indexed_files = set(self.state.keys())
        deleted_files = indexed_files - set(current_files.keys())
        
        if deleted_files:
            logger.info("Found orphaned files to remove from index", count=len(deleted_files))
            ids_to_delete = []
            for file_path_str in deleted_files:
                results = self.collection.get(where={"source": file_path_str}, include=[])
                ids_to_delete.extend(results['ids'])
                self.state.pop(file_path_str, None)
            
            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                logger.info("Removed orphaned chunks from ChromaDB.", count=len(ids_to_delete))

        files_to_index = []
        for rel_path_str, file_path in current_files.items():
            try:
                new_hash = self._calculate_hash(file_path)
                if self.state.get(rel_path_str) != new_hash:
                    files_to_index.append((file_path, new_hash))
            except Exception as e:
                logger.error("Could not process file", file=rel_path_str, error=str(e))
        
        if not files_to_index:
            logger.info("No new or modified files to index. Project is up to date.")
            self._save_state()
            self._create_manifest() # Still create manifest to update timestamp/commit
            return

        logger.info("Found new or modified files to index", count=len(files_to_index))
        
        total_chunks_to_embed = []
        file_hashes_to_update = {}

        for file_path, new_hash in files_to_index:
            rel_path_str = str(file_path.relative_to(self.project_root))
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                chunks = self._chunk_text(content, file_path)
                
                valid_chunks = []
                for i, chunk in enumerate(chunks):
                    if self._is_chunk_valid(chunk):
                        chunk_id = f"{rel_path_str}:{i}"
                        metadata = {"source": rel_path_str, "chunk_index": i}
                        valid_chunks.append({"id": chunk_id, "document": chunk, "metadata": metadata})
                
                if valid_chunks:
                    total_chunks_to_embed.extend(valid_chunks)
                    file_hashes_to_update[rel_path_str] = new_hash
            except Exception as e:
                logger.error("Error chunking file", file=rel_path_str, error=str(e))

        if not total_chunks_to_embed:
            logger.info("No valid new chunks to embed.")
            self._save_state()
            self._create_manifest()
            return

        logger.info("Total valid chunks to process", count=len(total_chunks_to_embed))  

        for i in range(0, len(total_chunks_to_embed), EMBEDDING_BATCH_SIZE):
            batch = total_chunks_to_embed[i:i+EMBEDDING_BATCH_SIZE]
            batch_texts = [item['document'] for item in batch]
            
            logger.info("Processing batch", current=i//EMBEDDING_BATCH_SIZE + 1, total=(len(total_chunks_to_embed) + EMBEDDING_BATCH_SIZE - 1)//EMBEDDING_BATCH_SIZE)
            
            embeddings = self.embed_provider.get_embeddings(batch_texts)
            
            if embeddings and len(embeddings) == len(batch):
                self.collection.upsert(
                    ids=[item['id'] for item in batch],
                    embeddings=embeddings,
                    documents=[item['document'] for item in batch],
                    metadatas=[item['metadata'] for item in batch]
                )
                for item in batch:
                    source_file = item['metadata']['source']
                    if source_file in file_hashes_to_update:
                        self.state[source_file] = file_hashes_to_update[source_file]
            else:
                logger.error("Failed to get embeddings for batch", first_chunk_id=batch[0]['id'])

        self._save_state()
        self._create_manifest()
        logger.info("Indexing process complete and manifest created.")

    def _get_current_commit_sha(self) -> Optional[str]:
        try:
            result = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True, cwd=self.project_root)
            return result.stdout.strip()
        except Exception as e:
            logger.warning("Could not determine current git commit SHA", error=str(e))
            return None

    def _create_manifest(self):
        manifest_path = self.index_path / "index_manifest.json"
        manifest_data = {
            "branch": self.branch,
            "commit_sha": self._get_current_commit_sha(),
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "embedding_provider": self.embedding_provider_name,
            "embedding_model": self.embed_provider.model_name
        }
        try:
            manifest_path.write_text(json.dumps(manifest_data, indent=2))
            logger.info("Created index manifest.", path=str(manifest_path))
        except Exception as e:
            logger.error("Failed to write index manifest", error=str(e))

# --- FIX 3: FULLY REFACTORED main() FUNCTION ---
def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="AI Assistant RAG Indexer")
    parser.add_argument("directory", nargs="?", default=".", help="The project directory to index.")
    parser.add_argument("--force-reindex", action="store_true", help="Force re-indexing of all files.")
    parser.add_argument("--branch", help="The git branch being indexed (for CI/CD). Overrides local git detection.")
    parser.add_argument(
        "--embedding-provider", 
        choices=["local", "openai"], 
        default="local", 
        help="The embedding provider to use (default: local)."
    )
    args = parser.parse_args()
    project_path = Path(args.directory).resolve()
    if not project_path.is_dir():
        logger.error("Path is not a valid directory", path=project_path)
        return
    try:
        indexer = Indexer(
            project_path, 
            branch_override=args.branch,
            embedding_provider=args.embedding_provider
        )
        indexer.run(force_reindex=args.force_reindex)
    except (ImportError, ConnectionError, ValueError) as e:
        logger.critical("Failed to initialize indexer", error=str(e))
        
if __name__ == "__main__":
    main()
