# .ai/plugins/local_trading_plugin.py
from typing import Dict, List
from pathlib import Path
import yaml
import re
from ai_assistant.context_plugin import ContextPluginBase

# This class name doesn't matter, the loader will find it.
class MyLocalTradingPlugin(ContextPluginBase):
    name = "LocalTrading"
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.config = self._load_project_config()

    def get_context(self, query: str, files: List[str]) -> str:
        if 'trading' not in query.lower():
            return "" # Query-aware: do nothing if not relevant

        print(f"   - {self.name} plugin: Trading keywords detected. Injecting local context.")
        
        context = "<LocalTradingPluginContext>\n"
        context += "  <SystemOverview>\n"
        context += "    This project contains trading services defined in .ai_config.yml.\n"
        context += f"    Legacy Service Path: {self.config.get('legacy_path', 'N/A')}\n"
        context += f"    New Service Path: {self.config.get('new_path', 'N/A')}\n"
        context += "  </SystemOverview>\n"
        context += "</LocalTradingPluginContext>\n"
        return context
        
    def _load_project_config(self) -> Dict:
        # Project-aware: reads the project-specific config file
        config_file = self.project_root / ".ai_config.yml"
        if not config_file.exists():
            return {}
        try:
            with open(config_file, 'r') as f:
                data = yaml.safe_load(f)
            services = data.get("trading", {}).get("services", [])
            legacy = next((s for s in services if s['name'] == 'MonolithicTradingService'), {})
            new = next((s for s in services if s['name'] == 'RefactoredTradingService'), {})
            return {"legacy_path": legacy.get('path'), "new_path": new.get('path')}
        except Exception:
            return {}
