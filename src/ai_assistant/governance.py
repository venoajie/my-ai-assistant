# src/ai_assistant/governance.py
import yaml
from importlib import resources
import structlog

logger = structlog.get_logger(__name__)

def _load_governance_rules():
    """Loads and parses the governance rules from the package data."""
    try:
        text = resources.files('ai_assistant').joinpath('internal_data/governance.yml').read_text(encoding='utf-8')
        return yaml.safe_load(text)
    except (FileNotFoundError, yaml.YAMLError) as e:
        logger.critical("FATAL: Could not load or parse governance.yml. The application cannot enforce its operational rules.", error=str(e))
        # In a real application, you might exit(1) here or raise a critical exception.
        return {}
