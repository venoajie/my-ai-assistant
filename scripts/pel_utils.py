# /scripts/pel_utils.py
from pathlib import Path
import yaml
from typing import Dict, Any, List

def load_config(path: Path) -> Dict[str, Any]:
    """Loads a YAML configuration file."""
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def find_all_personas(start_dir: Path) -> List[Path]:
    """
    Finds all .persona.md files within the specified directory,
    which should be the project's canonical persona location.
    """
    # MODIFIED: Point directly to the packaged personas directory
    persona_root = start_dir / "src" / "ai_assistant" / "personas"
    if not persona_root.exists():
        return []
    return list(persona_root.rglob("*.persona.md"))