# ai_assistant/trading_context.py
from typing import Dict, List, Any
from pathlib import Path
import yaml

from ai_assistant.context_plugin import ContextPluginBase

class TradingContextAnalyzer:
    """Specialized context analysis for trading applications"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.services_map = self._build_services_map()
        self.trading_concepts = self._load_trading_concepts()
    
    def analyze_service_context(self, file_path: str) -> Dict[str, Any]:
        """Understand which trading service we're working with"""
        path = Path(file_path)
        
        # Determine service from path
        service_name = None
        if 'services' in path.parts:
            service_idx = path.parts.index('services')
            if service_idx + 1 < len(path.parts):
                service_name = path.parts[service_idx + 1]
        
        context = {
            "service": service_name,
            "service_purpose": self.services_map.get(service_name, {}).get("purpose"),
            "dependencies": self._get_service_dependencies(service_name),
            "related_files": self._get_related_service_files(service_name)
        }
        
        return context
    
    def get_trading_domain_context(self, query: str) -> str:
        """Add trading-specific knowledge to context"""
        trading_keywords = ["order", "position", "risk", "pnl", "strategy", 
                          "market", "price", "volume", "execution", "latency"]
        
        if any(keyword in query.lower() for keyword in trading_keywords):
            return """
<TradingDomainKnowledge>
System Architecture:
- Receiver: WebSocket connections to exchanges (Binance, Deribit)  
- Distributor: Real-time data processing and OHLC aggregation
- Executor: Order management and strategy execution
- Analyzer: Technical analysis and signal generation
- Janitor: Data maintenance and cleanup

Key Concepts:
- All market data flows: Receiver → Distributor → Executor/Analyzer
- Risk management integrated at executor level
- Real-time position tracking and PnL calculation
- Multi-exchange support with unified interface
</TradingDomainKnowledge>
"""
        return ""

    def _build_services_map(self) -> Dict[str, Dict[str, Any]]:
        """Build map of services and their purposes"""
        config_file = self.project_root / ".ai_config.yml"
        if config_file.exists():
            with open(config_file) as f:
                config = yaml.safe_load(f)
            return {s["name"]: s for s in config.get("trading", {}).get("services", [])}
        return {}
    
    
class TradingContextPlugin(ContextPluginBase):
    name = "Trading"
    
    def get_context(self, query: str, files: List[str]) -> str:
        # All the logic from your current TradingContextAnalyzer goes here.
        # For example:
        trading_keywords = ["order", "position", "risk", "pnl", "strategy"]
        if any(keyword in query.lower() for keyword in trading_keywords):
            return """
<TradingDomainKnowledge>
- Receiver: WebSocket connections to exchanges...
- ... etc ...
</TradingDomainKnowledge>
"""
        return ""