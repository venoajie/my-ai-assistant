# src/ai_assistant/context_optimizer.py
from typing import Set, List
from .config import ai_settings

class ContextOptimizer:
    """
    Optimizes context for token efficiency by trimming and compressing text.
    """
    CHARS_PER_TOKEN_ESTIMATE: int = 4
    DEFAULT_MAX_TOKENS: int = 8000
    TRIM_SUMMARY_LINES: int = 10
    COMPRESS_CONTEXT_LINES: int = 2

    def __init__(self, max_tokens: int = None):
        """
        Initializes the optimizer with a maximum token limit.
        """
        self.max_tokens = max_tokens or getattr(ai_settings.context_optimizer, 'max_tokens', self.DEFAULT_MAX_TOKENS)

    def estimate_tokens(self, text: str) -> int:
        """
        Provides a rough estimation of token count based on character length.
        1 token is approximated as 4 characters.
        """
        return len(text) // self.CHARS_PER_TOKEN_ESTIMATE

    def trim_to_limit(self, text: str, max_tokens: int = None) -> str:
        """
        Trims text to fit within a specified token limit by keeping the start
        and end of the text, replacing the middle with an informative message.
        """
        limit = max_tokens or self.max_tokens
        max_chars = limit * self.CHARS_PER_TOKEN_ESTIMATE

        if len(text) <= max_chars:
            return text

        keep_chars_each_side = max_chars // 2
        if keep_chars_each_side <= 0:
            return text[:max_chars]

        truncated_chars = len(text) - (keep_chars_each_side * 2)
        if truncated_chars <= 0:
            return text[:max_chars]

        truncation_message = f"\n\n[... {truncated_chars} characters truncated ...]\n\n"
        return (text[:keep_chars_each_side] + truncation_message + text[-keep_chars_each_side:])

    def compress_file_context(self, file_path: str, content: str, query: str) -> str:
        """
        Compresses file content based on query relevance. It first tries to find
        lines matching the query keywords and includes context around them. If no
        matches are found, it falls back to a summary of the file's start and end.
        """
        lines = content.split('\n')
        query_keywords: Set[str] = set(query.lower().split())

        if not query_keywords:
            return self._summarize_by_lines(lines)

        indices_to_include: Set[int] = set()
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in query_keywords):
                start = max(0, i - self.COMPRESS_CONTEXT_LINES)
                end = min(len(lines), i + self.COMPRESS_CONTEXT_LINES + 1)
                for j in range(start, end):
                    indices_to_include.add(j)

        if indices_to_include:
            relevant_lines: List[str] = []
            last_index = -2
            for index in sorted(list(indices_to_include)):
                if index > last_index + 1 and last_index != -2:
                    relevant_lines.append('# ...')
                relevant_lines.append(lines[index])
                last_index = index
            return '\n'.join(relevant_lines)

        return self._summarize_by_lines(lines)

    def _summarize_by_lines(self, lines: List[str]) -> str:
        """
        Creates a summary of a file by taking the first and last N lines.
        """
        if len(lines) <= (self.TRIM_SUMMARY_LINES * 2):
            return '\n'.join(lines)

        truncated_line_count = len(lines) - (self.TRIM_SUMMARY_LINES * 2)
        truncation_message = f"# ... {truncated_line_count} lines truncated ..."
        return '\n'.join(lines[:self.TRIM_SUMMARY_LINES] + [truncation_message] + lines[-self.TRIM_SUMMARY_LINES:])