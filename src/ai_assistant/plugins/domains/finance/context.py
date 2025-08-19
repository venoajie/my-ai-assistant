# src\ai_assistant\plugins\domains\finance\context.py
from typing import Dict, Any, List, Optional
from pathlib import Path
from ai_assistant.context_plugin import ContextPluginBase

class FinanceContextPlugin(ContextPluginBase):
    name = "Finance"

    # Add the __init__ method to accept the project_root
    def __init__(self, project_root: Path):
        super().__init__(project_root)

    def get_context(self, query: str, files: List[str]) -> str:
        context = ""
        query_lower = query.lower()

        if 'api' in query_lower or 'contract' in query_lower:
            context += "<Knowledge source='FinancePlugin:API'>\n"
            context += "  - Financial APIs must prioritize idempotency for all transactional endpoints.\n"
            context += "  - Use standard HTTP status codes: 400 for validation errors, 402 for payment required.\n"
            context += "  - All monetary values should be represented as integers (cents) to avoid floating-point errors.\n"
            context += "</Knowledge>\n"
        
        return context
