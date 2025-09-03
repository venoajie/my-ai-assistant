# src/ai_assistant/plugins/rag_plugin.py

import asyncio
from pathlib import Path
from typing import List, Tuple, Optional
import structlog
import aiohttp

from ..config import ai_settings
from ..context_plugin import ContextPluginBase

logger = structlog.get_logger()

class RAGContextPlugin(ContextPluginBase):
    name = "Codebase-Aware RAG"

    def __init__(self, project_root: Path):
        super().__init__(project_root)
        self.librarian_url = ai_settings.rag.librarian_url
        if not self.librarian_url:
            self.is_ready = False
            self.message = "Librarian service URL is not configured in settings."
            logger.error(self.message)
        else:
            self.is_ready = True
            self.message = "RAG plugin ready to query Librarian service."
        self._status_cache = None

    def get_status_message(self) -> Optional[str]:
        """Synchronously fetches status from the Librarian service."""
        if not self.is_ready:
            return f"🧠 RAG Status: {self.message}"
        
        # Use a simple cache to avoid spamming the health endpoint
        if self._status_cache:
            return self._status_cache

        try:
            # Bridge async call in sync method
            status_data = asyncio.run(self._fetch_status())
            branch = status_data.get("index_branch", "unknown")
            collection = status_data.get("chroma_collection", "unknown")
            index_status = status_data.get("index_status", "unknown").upper()
            
            self._status_cache = f"🧠 RAG Status ({index_status}) | Branch: {branch} | Collection: {collection}"
            return self._status_cache
        except Exception as e:
            logger.error("Failed to get RAG status from Librarian", error=str(e))
            return "🧠 RAG Status: UNREACHABLE"

    async def _fetch_status(self) -> dict:
        health_url = f"{self.librarian_url.rstrip('/')}/health"
        async with aiohttp.ClientSession() as session:
            async with session.get(health_url, timeout=5) as response:
                response.raise_for_status()
                return await response.json()

    async def get_context_async(self, query: str) -> Tuple[bool, str]:        
        """Asynchronously fetches context from the Librarian service."""
        if not self.is_ready:
            return False, self.message
        
        context_url = f"{self.librarian_url.rstrip('/')}/api/v1/context"
        try:
            payload = {
                "query": query,
                "max_results": ai_settings.rag.rerank_top_n,
            }
            headers = {"X-API-Key": ai_settings.rag.librarian_api_key}

            logger.info("Querying Librarian service for RAG context...", url=context_url)
            async with aiohttp.ClientSession() as session:
                async with session.post(context_url, json=payload, headers=headers, timeout=30) as response:
                    if response.status != 200:
                        error_detail = await response.text()
                        logger.error(
                            "Librarian service returned an error",
                            status=response.status,
                            detail=error_detail,
                        )
                        return False, f"Librarian service error ({response.status}): {error_detail}"

                    data = await response.json()
                    context_chunks = data.get("context", [])

                    if not context_chunks:
                        return True, "<Context>No relevant documents found in the codebase for the query.</Context>"

                    context_str = "\n\n---\n\n".join(
                        f"<ContextChunk source=\"{chunk.get('metadata', {}).get('source', 'unknown')}\">\n{chunk['content']}\n</ContextChunk>"
                        for chunk in context_chunks
                    )
                    return True, context_str
        except Exception as e:
            logger.error("RAG context retrieval failed", error=str(e), exc_info=True)
            return False, f"Failed to get context from Librarian service: {e}"