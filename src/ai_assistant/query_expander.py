# src/ai_assistant/query_expander.py
from pathlib import Path
from typing import List

import structlog

from .config import ai_settings
from .response_handler import ResponseHandler

logger = structlog.get_logger(__name__)

def gather_high_level_context(auto_inject_files: List[str]) -> str:
    """Gathers high-level context from a list of auto-injected files."""
    high_level_context_str = ""
    if not auto_inject_files:
        return ""
        
    logger.info("Gathering high-level context for query expansion.", files=auto_inject_files)
    for file_path_str in auto_inject_files:
        path = Path(file_path_str)
        if path.exists() and path.is_file():
            try:
                high_level_context_str += f"\n--- Context from {file_path_str} ---\n"
                high_level_context_str += path.read_text(encoding='utf-8', errors='ignore')
            except Exception as e:
                logger.warning("Could not read auto-injected file for context.", file=file_path_str, error=str(e))
    return high_level_context_str

async def expand_query_with_context(query: str, high_level_context: str) -> str:
    """Uses an LLM to expand a user query with project-specific context."""
    if not high_level_context.strip():
        logger.info("No high-level context provided for query expansion. Skipping.")
        return query

    expansion_prompt = f"""You are a search query optimization expert for a software project.
Your task is to expand a user's query to be more effective for a semantic search against the project's codebase.
Use the provided <ProjectContext> to make the expansion specific and relevant. The final output should be a single, optimized query string.

<ProjectContext>
{high_level_context}
</ProjectContext>

<UserQuery>
{query}
</UserQuery>

Optimized Search Query:"""

    try:
        handler = ResponseHandler()
        # Use a fast and cheap model for this task
        expansion_model = ai_settings.model_selection.query_expander
        result = await handler.call_api(expansion_prompt, model=expansion_model, generation_config={"temperature": 0.0})
        expanded_query = result["content"].strip()
        
        if expanded_query:
             logger.info("Successfully expanded user query.", original=query, expanded=expanded_query)
             return expanded_query
        else:
             logger.warning("Query expansion returned an empty string. Falling back to original query.")
             return query
    except Exception as e:
        logger.warning("Query expansion failed. Falling back to original query.", error=str(e))
        return query