# plugins/trading_plugin.py 
from typing import Dict, List, Optional
from pathlib import Path
import yaml
import re
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
        # Keywords that trigger this plugin's context injection.
        self.trigger_keywords = [
            'trade', 'trading', 'order', 'market', 'exchange', 
            'fix engine', 'oms', 'ems', 'service'
        ]

    def get_context(self, query: str, files: List[str]) -> str:
        """
        Analyzes the query for trading-related keywords. If found, injects
        context about the project's trading services defined in .ai_config.yml.
        """
        # Use regex for more robust keyword matching (whole words only)
        if not any(re.search(r'\b' + keyword + r'\b', query, re.IGNORECASE) for keyword in self.trigger_keywords):
            return "" # No keywords found, provide no context.

        if not self.services_map:
            return "" # No services defined, nothing to add.

        print(f"   - {self.name} plugin: Trading keywords detected. Injecting service context.")
        
        context = "<TradingContext>\n"
        context += "  <SystemOverview>\n"
        context += "    This project contains a high-frequency trading system. The following services have been defined in the project configuration:\n"
        context += "  </SystemOverview>\n"
        context += "  <Services>\n"
        for name, service_data in self.services_map.items():
            description = service_data.get('description', 'No description provided.')
            path = service_data.get('path', 'N/A')
            context += f"    <Service name='{name}' path='{path}'>\n"
            context += f"      {description}\n"
            context += f"    </Service>\n"
        context += "  </Services>\n"
        context += "</TradingContext>\n\n"
        
        return context
        
    def _build_services_map(self) -> Dict:
        """
        Loads service definitions from the project's .ai_config.yml file.
        This demonstrates how a plugin can be project-aware.
        """
        config_file = self.project_root / ".ai_config.yml"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                # Safely navigate the dictionary
                services = config_data.get("trading", {}).get("services", [])
                if isinstance(services, list):
                    return {s["name"]: s for s in services if isinstance(s, dict) and "name" in s}
            except (yaml.YAMLError, KeyError, TypeError) as e:
                print(f"   - ⚠️ Warning (Trading Plugin): Could not parse services from .ai_config.yml: {e}")
        return {}