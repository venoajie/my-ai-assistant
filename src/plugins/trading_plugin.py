# plugins/trading_plugin.py 
from typing import Dict, List
from pathlib import Path
import yaml
from ai_assistant.context_plugin import ContextPluginBase

class TradingContextPlugin(ContextPluginBase):
    """
    Provides domain-specific context for high-frequency trading applications.
    It injects knowledge about system architecture and key trading concepts
    when relevant keywords are detected in the user's query.
    """
    name = "Trading"
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.services_map = self._build_services_map()
    

        self.project_root = project_root

    def get_context(self, query: str, files: List[str]) -> str:
        context = ""
        trading_config_path = self.project_root / "trading-config.yml"
        
        if trading_config_path.exists():
            context += "<TradingContext>\n"
            context += f"Found trading configuration at: {trading_config_path}\n"
            # You could even read and inject parts of the config here
            context += "</TradingContext>\n\n"
        
        return context
        
    def _build_services_map(self) -> Dict:
        """
        Loads service definitions from the project's .ai_config.yml file.
        This is an example of how a plugin can be project-aware.
        """
        config_file = self.project_root / ".ai_config.yml"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    config_data = yaml.safe_load(f)
                    return {s["name"]: s for s in config_data.get("trading", {}).get("services", [])}
            except (yaml.YAMLError, KeyError, TypeError) as e:
                print(f"   - ⚠️ Warning: Could not parse services from .ai_config.yml: {e}")
        return {}