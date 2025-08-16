# src/ai_assistant/utils/signature.py
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Any

def calculate_persona_signature(
    persona_details: List[Dict[str, Any]], 
    project_root: Path,
    ) -> str:
    
    """
    Calculates a deterministic signature based on persona content and structure.
    This is the canonical implementation used by both the manifest generator
    and the runtime CLI validator.

    Args:
        persona_details: A list of dictionaries, each containing details about a validated persona.
        project_root: The absolute path to the project's root directory.

    Returns:
        A SHA256 hexdigest representing the signature of all persona content.
    """
    canonical_data = []
    # Sort by alias to ensure a deterministic order
    for details in sorted(persona_details, key=lambda p: p['alias']):
        canonical_data.append({
            "alias": details['alias'],
            "path": str(details['path'].relative_to(project_root)),
            "content_sha256": hashlib.sha256(details['content'].encode('utf-8')).hexdigest(),
        })
    
    # Use separators=(',', ':') to create the most compact, deterministic JSON string
    canonical_string = json.dumps(
        canonical_data, 
        sort_keys=True, 
        separators=(',', ':'),
        )
    
    return hashlib.sha256(canonical_string.encode('utf-8')).hexdigest()