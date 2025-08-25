# src/ai_assistant/utils/git_utils.py
import subprocess
from pathlib import Path

def get_normalized_branch_name(cwd: Path, default: str) -> str:
    """Gets the current git branch and normalizes it for use in collection names."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True, text=True, check=True, cwd=cwd
        )
        # Replace slashes and other potentially problematic characters
        return result.stdout.strip().replace('/', '_').replace('\\', '_')
    except Exception:
        return default