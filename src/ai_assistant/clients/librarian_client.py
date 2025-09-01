# src/ai_assistant/clients/librarian_client.py

import os
import aiohttp
import structlog
from typing import List, Dict, Any, Optional

logger = structlog.get_logger(__name__)

# Load configuration from environment variables
LIBRARIAN_API_URL = os.getenv("LIBRARIAN_API_URL")
LIBRARIAN_API_KEY = os.getenv("LIBRARIAN_API_KEY")

# A global session object to be managed
_session: Optional[aiohttp.ClientSession] = None

async def get_session() -> aiohttp.ClientSession:
    """
    Returns a shared, singleton aiohttp.ClientSession.
    This prevents creating new connections for every request.
    """
    global _session
    if _session is None or _session.closed:
        headers = {"X-API-KEY": LIBRARIAN_API_KEY}
        timeout = aiohttp.ClientTimeout(total=15.0)
        _session = aiohttp.ClientSession(headers=headers, timeout=timeout)
    return _session

async def close_session():
    """Closes the shared session. Should be called on application shutdown."""
    global _session
    if _session and not _session.closed:
        await _session.close()
        _session = None

async def get_context_from_librarian(
    query: str, 
    max_results: int = 5
) -> Optional[List[Dict[str, Any]]]:
    """
    Asynchronously retrieves context from the Librarian service using aiohttp.

    Args:
        query: The search query string.
        max_results: The desired number of context chunks.

    Returns:
        A list of context chunk dictionaries, or None if an error occurs.
    """
    if not LIBRARIAN_API_URL or not LIBRARIAN_API_KEY:
        logger.error("LIBRARIAN_API_URL and LIBRARIAN_API_KEY must be set.")
        return None

    request_url = f"{LIBRARIAN_API_URL.strip('/')}/api/v1/context"
    request_body = {"query": query, "max_results": max_results}

    try:
        session = await get_session()
        async with session.post(request_url, json=request_body) as response:
            # Raise an exception for 4xx or 5xx status codes
            response.raise_for_status()
            
            data = await response.json()
            logger.info(
                f"Successfully retrieved {len(data.get('context', []))} chunks "
                f"from Librarian in {data.get('processing_time_ms')}ms."
            )
            return data.get("context")

    except aiohttp.ClientResponseError as e:
        # aiohttp provides status and message directly on the exception
        error_text = await e.text()
        logger.error(f"HTTP error calling Librarian: {e.status} - {error_text}")
    except aiohttp.ClientError as e:
        # Catches other connection-related errors (e.g., DNS, timeout)
        logger.error(f"Request error calling Librarian: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in the Librarian client: {e}")
        
    return None