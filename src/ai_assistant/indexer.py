# src/ai_assistant/indexer.py


import argparse
import hashlib
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator
import fnmatch
import subprocess
from datetime import datetime, timezone
import ast
from collections import defaultdict

try:
    from sentence_transformers import SentenceTransformer
    from openai import OpenAI
    from sqlalchemy import create_engine, text, insert, table, column, String, JSON, TEXT
    from pgvector.sqlalchemy import VECTOR
    import psycopg2
    import oci
    import orjson
except ImportError:
    # This will be caught by the check in main()
    SentenceTransformer, OpenAI, create_engine, psycopg2, oci, orjson = (None,)*6

import structlog
from dotenv import load_dotenv

from .config import ai_settings
from .logging_config import setup_logging
from .utils.git_utils import get_normalized_branch_name

load_dotenv()
logger = structlog.get_logger()

EMBEDDING_BATCH_SIZE = 16
DEFAULT_IGNORE_PATTERNS = [".git/", ".venv/", "venv/", "__pycache__/", "*.pyc", "*.log", ".DS_Store", "node_modules/", "build/", "dist/", ".idea/", ".vscode/", "*.egg-info/", "src/ai_assistant/personas/", ".ai/personas/", "src/ai_assistant/internal_data/"]

LANGUAGE_MAP = {
    '.py': 'python', '.js': 'javascript', '.ts': 'typescript', '.md': 'markdown',
    '.java': 'java', '.go': 'go', '.rs': 'rust', '.html': 'html', '.css': 'css',
    '.cpp': 'cpp', '.c': 'c', '.cs': 'csharp', '.rb': 'ruby', '.php': 'php',
    '.swift': 'swift', '.kt': 'kotlin', '.sh': 'bash', '.sql': 'sql',
    '.yaml': 'yaml', '.yml': 'yaml', '.json': 'json'
}

class EmbeddingProvider:
    # ... (This class is well-designed and requires no changes) ...
    def __init__(self, provider_name: str = "local"):
        self.provider_name = provider_name
        
        if self.provider_name == "local":
            self.model_name = ai_settings.rag.embedding_model_name
            logger.info("Loading local embedding model", model_name=self.model_name)
            if not SentenceTransformer:
                raise ImportError("sentence-transformers is not installed. Please run 'pip install -e .[indexing]'")
            self.model = SentenceTransformer(self.model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info("Local model loaded successfully.", embedding_dim=self.embedding_dim)
        elif self.provider_name == "openai":
            if not OpenAI:
                raise ImportError("openai library is not installed. Please run 'pip install openai'.")
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set.")
            self.client = OpenAI(api_key=api_key)
            self.model_name = "text-embedding-3-large"
            self.embedding_dim = 3072 
            logger.info("Using OpenAI embedding provider", model_name=self.model_name)
        else:
            raise ValueError(f"Unsupported embedding provider: {provider_name}")

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts: return []
        
        if self.provider_name == "local":
            return [emb.tolist() for emb in self.model.encode(texts, show_progress_bar=True)]
        elif self.provider_name == "openai":
            response = self.client.embeddings.create(input=texts, model=self.model_name)
            return [item.embedding for item in response.data]
        return []

class Indexer:
    def __init__(
        self,
        project_root: Path,
        branch_override: Optional[str] = None,
        embedding_provider: str = "local",
        database_url_override: Optional[str] = None,
    ):
        self.project_root = project_root
        self.staging_path = project_root / ai_settings.rag.local_index_path
        self.state_path = self.staging_path / "state.json"
        self.manifest_path = self.staging_path / "index_manifest.json"
        self.staging_path.mkdir(exist_ok=True)

        db_url = database_url_override or ai_settings.rag.database_url
        if not db_url:
            raise ValueError("DATABASE_URL is not configured via command-line, settings, or environment variables.")
                
        self.engine = create_engine(db_url)
        
        if embedding_provider != "local":
            raise ValueError("FATAL: The indexer only supports 'local' embedding provider for production RAG.")
        
        self.active_provider = EmbeddingProvider(embedding_provider)
        logger.info(f"Successfully initialized '{embedding_provider}' as the embedding provider.")
            
        # --- Get the project name from the environment, default to repo name ---
        project_name = os.getenv("PROJECT_NAME", self.project_root.name)
        sanitized_project = re.sub(r'[^a-zA-Z0-9_]', '_', project_name)

        self.branch = branch_override or get_normalized_branch_name(self.project_root, ai_settings.rag.default_branch)
        sanitized_branch = re.sub(r'[^a-zA-Z0-9_]', '_', self.branch)
        
        # --- Make the table name unique per project AND per branch ---
        self.table_name = f"{ai_settings.rag.collection_name}_{sanitized_project}_{sanitized_branch}"
        
        logger.info("Indexer targeting database table", table_name=self.table_name)

        self.table = table(
            self.table_name,
            column("id", String),
            column("content", TEXT),
            column("metadata", JSON),
            column("embedding", VECTOR(self.active_provider.embedding_dim))
        )

        self.state = self._load_state()
        self.ignore_patterns = self._load_ignore_patterns()
        self._init_database()

    def _init_database(self):
        try:
            with self.engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.commit()
            logger.info("Successfully enabled 'vector' extension in PostgreSQL.")
        except Exception as e:
            logger.critical("Failed to connect to the database or enable vector extension.", error=str(e))
            raise

    def _setup_database_table(self):
        create_table_sql = text(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id VARCHAR(1024) PRIMARY KEY,
                content TEXT NOT NULL,
                metadata JSONB,
                embedding VECTOR({self.active_provider.embedding_dim})
            );
        """)
        
        create_index_sql = text(f"""
            CREATE INDEX ON {self.table_name} USING hnsw (embedding vector_cosine_ops);
        """)
        
        try:
            with self.engine.begin() as conn:
                conn.execute(create_table_sql)
                # We wrap the index creation in its own try/except block
                # to gracefully handle the case where it already exists.
                try:
                    conn.execute(create_index_sql)
                    logger.info("Successfully created HNSW index.", table=self.table_name)
                except Exception as e:
                    # Check if the error is because the index already exists
                    if "already exists" in str(e):
                        logger.info("HNSW index already exists, skipping creation.", table=self.table_name)
                    else:
                        # If it's a different error, we should raise it
                        raise
            logger.info("Database table and HNSW index are ready.", table=self.table_name)
        except Exception as e:
            logger.critical("Failed to create database table or index.", table=self.table_name, error=str(e))
            raise
        
    def _load_state(self) -> Dict[str, str]:
        if self.state_path.exists():
            with open(self.state_path, 'rb') as f:
                return orjson.loads(f.read())
        return {}

    def _save_state(self):
        # --- REFACTOR: Atomic write to prevent state file corruption ---
        temp_path = self.state_path.with_suffix('.tmp')
        with open(temp_path, 'wb') as f:
            f.write(orjson.dumps(self.state, option=orjson.OPT_INDENT_2))
        temp_path.replace(self.state_path)

    # ... (No changes needed for _load_ignore_patterns, _is_ignored, _walk_project, _calculate_hash, _is_chunk_valid, _extract_file_metadata, _chunk_file) ...
    def _load_ignore_patterns(self) -> List[str]:
        patterns = DEFAULT_IGNORE_PATTERNS
        patterns.append(str(self.staging_path.relative_to(self.project_root)) + "/*")
        ignore_file = self.project_root / ".aiignore"
        if ignore_file.exists():
            with open(ignore_file, 'r') as f:
                patterns.extend([line.strip() for line in f if line.strip() and not line.startswith('#')])
        return patterns

    def _is_ignored(self, path: Path) -> bool:
        rel_path_str = os.path.normpath(str(path.relative_to(self.project_root)))
        for pattern in self.ignore_patterns:
            norm_pattern = os.path.normpath(pattern)
            if fnmatch.fnmatch(rel_path_str, norm_pattern) or (norm_pattern.endswith(os.sep) and (rel_path_str + os.sep).startswith(norm_pattern)):
                return True
        return False

    def _walk_project(self) -> Generator[Path, None, None]:
        for root, dirs, files in os.walk(self.project_root, topdown=True):
            root_path = Path(root)
            dirs[:] = [d for d in dirs if not self._is_ignored(root_path / d)]
            for name in files:
                file_path = root_path / name
                if not self._is_ignored(file_path):
                    yield file_path
                        
    @staticmethod
    def _calculate_hash(file_path: Path) -> str:
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while buf := f.read(65536): hasher.update(buf)
        return hasher.hexdigest()

    @staticmethod
    def _is_chunk_valid(chunk: str, min_length: int = 20) -> bool:
        return len(chunk.strip()) >= min_length and (len(chunk.strip()) / len(chunk)) > 0.5 and '\x00' not in chunk

    def _extract_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        rel_path_str = str(file_path.relative_to(self.project_root))
        service_match = re.search(r'src/(?:services/)?([^/]+)/', rel_path_str)
        return {
            'language': LANGUAGE_MAP.get(file_path.suffix.lower(), 'unknown'),
            'is_test_file': ('/tests/' in rel_path_str or '/test/' in rel_path_str or file_path.name.startswith('test_')),
            'service_name': service_match.group(1) if service_match else 'unknown'
        }

    def _chunk_file(self, text: str, file_path: Path) -> List[Dict[str, Any]]:
        chunks_with_metadata = []
        if file_path.suffix.lower() == '.py':
            try:
                tree = ast.parse(text)
                source_lines = text.splitlines()
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        start_line = node.lineno - 1
                        end_line = node.end_lineno or start_line + 1
                        chunk_text = "\n".join(source_lines[start_line:end_line])
                        if self._is_chunk_valid(chunk_text):
                            chunks_with_metadata.append({
                                "text": chunk_text,
                                "metadata": {"entity_type": "class" if isinstance(node, ast.ClassDef) else "function", "name": node.name, "start_line": node.lineno, "end_line": end_line}
                            })
                if not chunks_with_metadata: raise SyntaxError("No functions/classes found")
            except (SyntaxError, ValueError):
                if self._is_chunk_valid(text):
                    chunks_with_metadata = [{"text": text, "metadata": {"entity_type": "file", "name": file_path.name}}]
        else:
            chunk_size, overlap = 1000, 200
            for i in range(0, len(text), chunk_size - overlap):
                chunk_text = text[i:i+chunk_size]
                if self._is_chunk_valid(chunk_text):
                    chunks_with_metadata.append({"text": chunk_text, "metadata": {"entity_type": "file", "name": file_path.name}})
        return chunks_with_metadata

    def run(self, force_reindex: bool = False):
        logger.info("Starting indexer", project_root=self.project_root, db_table=self.table_name)
        
        try:
            self._setup_database_table()

            if force_reindex:
                logger.warning("Forcing re-index of all files and clearing table.")
                self.state = {}
                with self.engine.begin() as conn:
                    conn.execute(text(f"TRUNCATE TABLE {self.table_name};"))

            current_files = {str(p.relative_to(self.project_root)): p for p in self._walk_project()}
            indexed_files = set(self.state.keys())
            deleted_files = indexed_files - set(current_files.keys())
            
            if deleted_files:
                logger.info("Found orphaned files to remove from index", count=len(deleted_files))
                with self.engine.begin() as conn:
                    for file_path_str in deleted_files:
                        conn.execute(text(f"DELETE FROM {self.table_name} WHERE metadata->>'source' = :file_path"), {"file_path": file_path_str})
                        self.state.pop(file_path_str, None)

            files_to_index = []
            for rel_path_str, file_path in current_files.items():
                try:
                    new_hash = self._calculate_hash(file_path)
                    if self.state.get(rel_path_str) != new_hash:
                        files_to_index.append((file_path, new_hash))
                except Exception as e:
                    logger.error("Could not process file, skipping.", file=rel_path_str, error=str(e))
            
            if not files_to_index:
                logger.info("No new or modified files to index. Project is up to date.")
            else:
                logger.info("Found new or modified files to index", count=len(files_to_index))
                self._process_files(files_to_index)

        finally:
            # This guarantees that our artifact files are always created.
            logger.info("Finalizing run: saving state and creating manifest.")
            self._save_state()
            self._create_manifest()
            
            # Only attempt upload if the main logic didn't crash before OCI config was checked.
            try:
                self._upload_artifacts_to_oci()
                logger.info("Indexing process and artifact upload complete.")
            except Exception as e:
                logger.critical("Artifact upload failed. The CI job should fail.", error=str(e))
                # Re-raise the exception to ensure the CI step fails.
                raise
            
    def _process_files(self, files_to_process: List[tuple[Path, str]]):
        chunks_by_file = defaultdict(list)
        file_hashes_to_update = {}

        for file_path, new_hash in files_to_process:
            rel_path_str = str(file_path.relative_to(self.project_root))
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                file_metadata = self._extract_file_metadata(file_path)
                for i, chunk_data in enumerate(self._chunk_file(content, file_path)):
                    chunk_id = f"{rel_path_str}:{i}"
                    final_metadata = {"source": rel_path_str, "chunk_index": i, **file_metadata, **chunk_data['metadata']}
                    chunks_by_file[rel_path_str].append({"id": chunk_id, "document": chunk_data['text'], "metadata": final_metadata})
                file_hashes_to_update[rel_path_str] = new_hash
            except Exception as e:
                logger.error("Error chunking file", file=rel_path_str, error=str(e))

        all_chunks = [chunk for chunks in chunks_by_file.values() for chunk in chunks]
        if not all_chunks:
            logger.warning("No valid chunks were produced from the files to be indexed.")
            return

        logger.info("Generating embeddings for all new/modified chunks", count=len(all_chunks))
        all_texts = [c['document'] for c in all_chunks]
        all_embeddings = self.active_provider.get_embeddings(all_texts)
        for chunk, embedding in zip(all_chunks, all_embeddings):
            chunk['embedding'] = embedding

        for rel_path_str, chunks in chunks_by_file.items():
            logger.info("Syncing file to database", file=rel_path_str, chunks=len(chunks))
            try:
                with self.engine.begin() as conn:
                    conn.execute(text(f"DELETE FROM {self.table_name} WHERE metadata->>'source' = :file_path"), {"file_path": rel_path_str})
                    if chunks:
                        conn.execute(insert(self.table), [
                            {"id": c['id'], "content": c['document'], "metadata": c['metadata'], "embedding": c['embedding']} for c in chunks
                        ])
                self.state[rel_path_str] = file_hashes_to_update[rel_path_str]
            except Exception as e:
                logger.error("Failed to sync file to database. Skipping.", file=rel_path_str, error=str(e))

    def _get_current_commit_sha(self) -> Optional[str]:
        try:
            return subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True, cwd=self.project_root).stdout.strip()
        except Exception:
            return None

    def _create_manifest(self):
        manifest_data = {
            "branch": self.branch,
            "commit_sha": self._get_current_commit_sha(),
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "embedding_provider": self.active_provider.provider_name,
            "embedding_model": self.active_provider.model_name,
            "db_table_name": self.table_name
        }
        with open(self.manifest_path, 'wb') as f:
            f.write(orjson.dumps(manifest_data, option=orjson.OPT_INDENT_2))
        logger.info("Created index manifest.", path=str(self.manifest_path))

    def _upload_artifacts_to_oci(self):
        # --- REFACTOR: Fail-fast OCI initialization ---
        oci_settings = ai_settings.rag.oracle_cloud
        if not (oci_settings and oci_settings.bucket and oci_settings.namespace):
            logger.warning("OCI configuration is incomplete in settings. Skipping upload.")
            return

        try:
            # This will raise an exception if config is invalid, failing the CI job correctly.
            oci_config = oci.config.from_file()
            object_storage_client = oci.object_storage.ObjectStorageClient(oci_config)
            logger.info("OCI Object Storage client initialized successfully for upload.")
        except Exception as e:
            logger.critical("FATAL: Failed to initialize OCI client. Check credentials and config.", error=str(e))
            raise

        project_name = os.getenv("PROJECT_NAME", self.project_root.name)
        artifacts = {"index_manifest.json": self.manifest_path, "state.json": self.state_path}

        for filename, local_path in artifacts.items():
            if local_path.exists():
                object_name = f"indexes/{project_name}/{self.branch}/latest/{filename}"
                logger.info("Uploading artifact to OCI", local_path=str(local_path), object_name=object_name)
                try:
                    with open(local_path, 'rb') as f:
                        object_storage_client.put_object(
                            namespace_name=oci_settings.namespace,
                            bucket_name=oci_settings.bucket,
                            object_name=object_name,
                            put_object_body=f,
                            if_match=None, # Overwrite unconditionally
                        )
                    logger.info("Successfully uploaded artifact.", filename=filename)
                except oci.exceptions.ServiceError as e:
                    logger.error("Failed to upload artifact to OCI.", filename=filename, status=e.status, message=e.message)
                    # Re-raise to ensure the CI job fails if the upload itself fails
                    raise
            else:
                logger.warning("Artifact not found locally, cannot upload.", filename=filename)

def main():
    setup_logging()
    
    if not all([SentenceTransformer, OpenAI, create_engine, psycopg2, oci, orjson]):
        logger.critical("FATAL: One or more required libraries for indexing are not installed. Please run 'pip install -e .[indexing]'")
        return

    parser = argparse.ArgumentParser(description="AI Assistant RAG Indexer")
    parser.add_argument("directory", nargs="?", default=".", help="The project directory to index.")
    parser.add_argument("--force-reindex", action="store_true", help="Force re-indexing of all files.")
    parser.add_argument("--branch", help="The git branch being indexed (for CI/CD). Overrides local git detection.")
    parser.add_argument(
        "--database-url",
        help="The PostgreSQL connection URL. Overrides any value from config files or .env."
    )
    args = parser.parse_args()
    
    try:
        indexer = Indexer(
            project_root=Path(args.directory), 
            branch_override=args.branch,
            database_url_override=args.database_url # Use the parsed arg here
        )
        indexer.run(force_reindex=args.force_reindex)
    except (ValueError, RuntimeError) as e:
        logger.critical("A configuration or runtime error occurred during indexer setup.", error=str(e))
    except Exception as e:
        logger.critical("An unexpected error occurred during the indexing process.", error=str(e), exc_info=True)
        
if __name__ == "__main__":
    main()