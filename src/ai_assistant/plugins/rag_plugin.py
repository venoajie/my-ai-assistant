# src/ai_assistant/plugins/rag_plugin.py

from pathlib import Path
from typing import List, Tuple
import structlog

from ..config import ai_settings
from ..context_plugin import ContextPluginBase
from ai_assistant.clients.librarian_client import get_context_from_librarian

logger = structlog.get_logger()

class RAGContextPlugin(ContextPluginBase):
    name = "Codebase-Aware RAG"

    def __init__(self, project_root: Path):
        super().__init__(project_root)
        self.is_ready = True
        self.message = "RAG client ready to connect to Librarian service."

    def get_status_message(self) -> str:
        # Provide a simple status message.
        return "🧠 RAG Status: Connected to central Librarian service."

    async def get_context(self, query: str, files: List[str]) -> Tuple[bool, str]:
        logger.info("Retrieving context from Librarian service...", query=query)
        
        # The core logic is now just one function call.
        context_chunks = await get_context_from_librarian(
            query, 
            max_results=ai_settings.rag.rerank_top_n
        )

        if context_chunks is None:
            # The client function handles logging the error.
            return (False, "Failed to retrieve context from the Librarian service.")

        if not context_chunks:
            return (True, "<Context>No relevant documents found in the codebase for the query.</Context>")

        # Format the response exactly as the old plugin did, for consistency.
        context_str = "\n\n---\n\n".join(
            f"<ContextChunk source=\"{chunk.get('metadata', {}).get('source', 'unknown')}\">\n{chunk.get('content', '')}\n</ContextChunk>"
            for chunk in context_chunks
        )
        
        return (True, context_str)