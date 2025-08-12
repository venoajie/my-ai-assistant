# /scripts/pel_utils.py
from pathlib import Path
import yaml
from typing import Dict, Any, List

def load_config(path: Path) -> Dict[str, Any]:
    """Loads a YAML configuration file with robust error handling."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                # Raise an error for empty files
                raise ValueError("Configuration file is empty.")
            
            data = yaml.safe_load(content)
            
            if not isinstance(data, dict):
                # Raise an error if the file is valid YAML but not a dictionary
                raise TypeError("Top-level content of configuration file is not a dictionary.")
                
            return data
    except FileNotFoundError:
        print(f"FATAL: Configuration file not found at {path}", file=sys.stderr)
        return None
    except (ValueError, TypeError, yaml.YAMLError) as e:
        print(f"FATAL: Failed to load or parse configuration file at {path}. Reason: {e}", file=sys.stderr)
        return None

def find_all_personas(start_dir: Path) -> List[Path]:
    """
    Finds all .persona.md files within the project's src directory.
    """
    persona_root = start_dir / "src" / "ai_assistant" / "personas"
    if not persona_root.exists():
        return []
    return list(persona_root.rglob("*.persona.md"))