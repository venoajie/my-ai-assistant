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
    
    def get_context(self, query: str, files: List[str]) -> str:
        """
        Analyzes the query for trading-related keywords and returns a
        context string if a match is found.
        """
        trading_keywords = [
            "order", "position", "risk", "pnl", "strategy", "market", 
            "price", "volume", "execution", "latency", "backtest", 
            "exchange", "receiver", "executor", "distributor"
        ]
        
        if any(kw in query.lower() for kw in trading_keywords):
            return """
<TradingDomainKnowledge>
System Architecture:
- Receiver: Manages WebSocket connections to exchanges (e.g., Binance, Deribit) for raw data ingestion.
- Distributor: Processes real-time data, aggregates it into OHLCV bars, and distributes to other services.
- Executor: Handles order lifecycle management (creation, submission, cancellation) and strategy execution.
- Analyzer: Performs technical analysis, generates trading signals, and runs backtests.
- Janitor: Responsible for data maintenance, cleanup, and archival.

Key Concepts:
- Data Flow: Market data flows unidirectionally: Receiver → Distributor → Executor/Analyzer.
- Risk Management: Integrated at the Executor level to check margin and position limits before placing orders.
- Position Tracking: Real-time PnL and position state are maintained across all active strategies.
- Multi-Exchange: The system uses a unified interface to abstract away differences between exchanges.
</TradingDomainKnowledge>
"""
        return ""
    
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