# src/ai_assistant/plugins/domains/trading/context.py
from typing import Dict, List, Optional
from pathlib import Path
import yaml
import re
from ai_assistant.context_plugin import ContextPluginBase

class TradingContextPlugin(ContextPluginBase):
    """
    Provides domain-specific context for high-frequency trading applications.
    This plugin serves as a best-practice example, demonstrating how to be:
    1.  **Project-Aware:** It reads project-specific configuration from `.ai_config.yml`.
    2.  **Query-Aware:** It only injects context when specific keywords are detected in the user's query.
    3.  **File-Aware:** It can analyze attached files to provide even more specific context.
    """
    name = "Trading"
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.services_map = self._load_project_config()
        # Keywords that trigger this plugin's context injection.
        self.trigger_keywords = [
            'trade', 'trading', 'order', 'market', 'exchange', 
            'fix engine', 'oms', 'ems', 'service', 'latency', 'venue'
        ]

    def get_context(self, query: str, files: List[str]) -> str:
        """
        Analyzes the query and files for trading-related keywords. If found,
        injects context about the project's trading services and architecture.
        """
        # Use regex for more robust keyword matching (whole words only)
        if not any(re.search(r'\b' + keyword + r'\b', query, re.IGNORECASE) for keyword in self.trigger_keywords):
            return "" # No keywords found, provide no context.

        if not self.services_map:
            return "" # No services defined, nothing to add.

        print(f"   - {self.name} plugin: Trading keywords detected. Injecting service context.")
        
        context_parts = []
        
        # --- Part 1: General System Overview ---
        context_parts.append("<TradingContext>")
        context_parts.append("  <SystemOverview>")
        context_parts.append("    This project is a high-frequency trading system. The following services are key components of its architecture, defined in the project configuration:")
        context_parts.append("  </SystemOverview>")
        context_parts.append("  <Services>")
        for name, service_data in self.services_map.items():
            description = service_data.get('description', 'No description provided.')
            path = service_data.get('path', 'N/A')
            context_parts.append(f"    <Service name='{name}' path='{path}'>")
            context_parts.append(f"      {description}")
            context_parts.append(f"    </Service>")
        context_parts.append("  </Services>")
        
        # --- Part 2: File-Aware Context ---
        # This demonstrates how a plugin can provide more specific context
        # by analyzing the files the user has attached to their prompt.
        file_specific_context = self._get_file_specific_context(files)
        if file_specific_context:
            context_parts.append("  <FileSpecificAnalysis>")
            context_parts.append(file_specific_context)
            context_parts.append("  </FileSpecificAnalysis>")

        context_parts.append("</TradingContext>\n")
        
        return "\n".join(context_parts)
        
    def _load_project_config(self) -> Dict:
        """
        Loads service definitions from the project's .ai_config.yml file.
        This demonstrates how a plugin can be project-aware.
        """
        config_file = self.project_root / ".ai_config.yml"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                # Safely navigate the dictionary to find the trading services
                services = config_data.get("trading", {}).get("services", [])
                if isinstance(services, list):
                    # Convert the list of service dicts into a map for easy lookup
                    return {s["name"]: s for s in services if isinstance(s, dict) and "name" in s}
            except (yaml.YAMLError, KeyError, TypeError) as e:
                print(f"   - ⚠️ Warning (Trading Plugin): Could not parse services from .ai_config.yml: {e}")
        return {}

    def _get_file_specific_context(self, file_paths: List[str]) -> str:
        """
        Analyzes attached file paths to see if they correspond to a known service.
        """
        relevant_services = []
        for file_path_str in file_paths:
            for service_name, service_data in self.services_map.items():
                service_path = service_data.get('path')
                if service_path and file_path_str.startswith(service_path):
                    if service_name not in relevant_services:
                        relevant_services.append(service_name)
        
        if not relevant_services:
            return ""
            
        if len(relevant_services) == 1:
            return f"    The attached files appear to be part of the '{relevant_services[0]}' service. Focus on the logic and responsibilities of this specific service."
        else:
            service_list = "', '".join(relevant_services)
            return f"    The attached files span multiple services: '{service_list}'. Pay close attention to the interactions and contracts between these services."