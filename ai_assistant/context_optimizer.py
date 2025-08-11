# ai_assistant/context_optimizer.py
from typing import Dict, List, Any
from .config import ai_settings

class ContextOptimizer:
    """Simple context optimization for token management"""
    
    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens or ai_settings.context_optimizer.max_tokens
    
    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 chars)"""
        return len(text) // 4
    
    def trim_to_limit(self, text: str, max_tokens: int = None) -> str:
        """Trim text to fit token limit"""
        limit = max_tokens or self.max_tokens
        max_chars = limit * 4
        
        if len(text) <= max_chars:
            return text
        
        # Simple trimming - keep start and end
        keep_start = max_chars // 2
        keep_end = max_chars // 2
        
        return (text[:keep_start] + 
                f"\n\n[... {len(text) - keep_start - keep_end} chars truncated ...]\n\n" + 
                text[-keep_end:])
    
    def compress_file_context(self, file_path: str, content: str, query: str) -> str:
        """Compress file content based on query relevance"""
        lines = content.split('\n')
        query_keywords = set(query.lower().split())
        
        relevant_lines = []
        context_size = 2  # Lines of context around matches
        
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in query_keywords):
                start = max(0, i - context_size)
                end = min(len(lines), i + context_size + 1)
                relevant_lines.extend(lines[start:end])
        
        if relevant_lines:
            return '\n'.join(set(relevant_lines))  # Remove duplicates
        
        # If no matches, return summary
        if len(lines) > 20:
            return '\n'.join(lines[:10] + ['# ... middle content truncated ...'] + lines[-10:])
        
        return content