# plugins/trading_plugin.py 
from typing import Dict, List
from pathlib import Path
import yaml
from ai_assistant.context_plugin import ContextPluginBase

class TradingContextPlugin(ContextPluginBase):
    name = "Trading"
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.services_map = self._build_services_map()
    
    def get_context(self, query: str, files: List[str]) -> str:
        trading_keywords = ["order", "position", "risk", "pnl", "strategy"]
        if any(kw in query.lower() for kw in trading_keywords):
            return """
<TradingDomainKnowledge>
System Architecture:
- Receiver: WebSocket connections to exchanges
- Distributor: Real-time data processing
- Executor: Order management
- Analyzer: Signal generation
- Janitor: Data maintenance

Key Concepts:
- Market data flows: Receiver → Distributor → Executor/Analyzer
- Real-time position tracking
- Multi-exchange support
</TradingDomainKnowledge>
"""
        return ""
    
    def _build_services_map(self) -> Dict:
        config_file = self.project_root / ".ai_config.yml"
        if config_file.exists():
            with open(config_file) as f:
                return {s["name"]: s for s in yaml.safe_load(f).get("trading", {}).get("services", [])}
        return {}