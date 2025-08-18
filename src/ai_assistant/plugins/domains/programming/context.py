from ai_assistant.context_plugin import ContextPluginBase
from typing import Dict, Any, List, Optional
from pathlib import Path

class ProgrammingContextPlugin(ContextPluginBase):
    name = "Programming"

    # Add the __init__ method to accept the project_root
    def __init__(self, project_root: Path):
        super().__init__(project_root)

    def get_context(self, query: str, files: List[str]) -> str:
        context = ""
        query_lower = query.lower()

        # Inject Alembic best practices if relevant
        if 'alembic' in query_lower or 'migration' in query_lower:
            context += "<Knowledge source='ProgrammingPlugin:Alembic'>\n"
            context += "  - Alembic migrations must have both upgrade and downgrade functions.\n"
            context += "  - Use `op.bulk_insert()` for data migrations to avoid per-row overhead.\n"
            context += "  - Always test migrations against a realistic database schema.\n"
            context += "</Knowledge>\n"

        # Inject security reminders if relevant
        if 'security' in query_lower or 'vulnerability' in query_lower:
            context += "<Knowledge source='ProgrammingPlugin:Security'>\n"
            context += "  - Always validate and sanitize user input to prevent injection attacks (OWASP A03).\n"

            context += "  - Never store secrets directly in source code or configuration files.\n"
            context += "  - Check for insecure direct object references (IDOR).\n"
            context += "</Knowledge>\n"
        
        return context
