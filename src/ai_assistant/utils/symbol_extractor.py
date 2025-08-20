# src/ai_assistant/utils/symbol_extractor.py
import ast
import inspect
from pathlib import Path
from typing import Optional

def extract_symbol_source(file_path: Path, symbol_name: str) -> Optional[str]:
    """
    Parses a Python file and extracts the full source code of a specific
    class or function.

    Args:
        file_path: The path to the Python file.
        symbol_name: The name of the class or function to extract.

    Returns:
        The source code of the symbol as a string, or None if not found.
    """
    try:
        source = file_path.read_text(encoding='utf-8')
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name == symbol_name:
                    # Use inspect.getsource on the original source text
                    # This is more reliable for getting comments and decorators
                    lines = source.splitlines()
                    start_line = node.lineno - 1
                    end_line = node.end_lineno
                    return "\n".join(lines[start_line:end_line])
        return None
    except Exception:
        return None # Fail silently if parsing fails