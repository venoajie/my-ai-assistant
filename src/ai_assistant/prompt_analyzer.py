# src/ai_assistant/prompt_analyzer.py
from dataclasses import dataclass
from typing import List, Optional, Dict, Callable
import re
from importlib import resources
import yaml

# --- Load the single source of truth once at module level ---
governance_text = resources.files('ai_assistant').joinpath('internal_data/governance.yml').read_text(encoding='utf-8')
GOVERNANCE_RULES = yaml.safe_load(governance_text)

@dataclass
class PromptViolation:
    rule_name: str
    severity: str
    message: str
    suggestion: Optional[str] = None

@dataclass
class AnalysisRule:
    name: str
    detector: Callable[[str, Dict], bool]
    severity: str
    message_template: str
    suggestion_template: Optional[str] = None

class PromptAnalyzer:
    """Analyzes prompts for best practice violations using configurable rules."""

    def __init__(self):
        # Read rules from the globally loaded governance object
        rules_config = GOVERNANCE_RULES.get('prompt_analysis_rules', [])
        self.rules = self._load_rules(rules_config)

    def _load_rules(
        self, 
        rules_config: List[Dict],
        ) -> List[AnalysisRule]:
        """Load analysis rules from the provided configuration list."""
        rules = []
        for rule_config in rules_config:
            detector = self._create_detector(rule_config['detector'])
            if detector:
                rules.append(AnalysisRule(
                    name=rule_config['name'],
                    detector=detector,
                    severity=rule_config['severity'],
                    message_template=rule_config['message'],
                    suggestion_template=rule_config.get('suggestion')
                ))
        return rules

    def _create_detector(
        self, 
        detector_config: Dict,
        ) -> Optional[Callable]:

        detector_type = detector_config.get('type')

        if detector_type == 'multi_file_action':
            return lambda prompt, ctx: (
                ctx.get('file_count', 0) > detector_config.get('threshold', 1) and
                any(word in prompt.lower() for word in detector_config.get('keywords', [])) and
                any(tag in prompt for tag in detector_config.get('required_tags', []))
            )
        
        elif detector_type == 'vague_instructions':
            vague_patterns = detector_config.get('patterns', [])
            return lambda prompt, ctx: any(
                re.search(pattern, prompt, re.IGNORECASE) 
                for pattern in vague_patterns
            )
        
        elif detector_type == 'missing_structure':
            required_tags = detector_config.get('required_tags', [])
            trigger_words = detector_config.get('trigger_words', [])
            return lambda prompt, ctx: (
                any(word in prompt.lower() for word in trigger_words) and
                not any(tag in prompt for tag in required_tags)
            )
        
        return None

    def analyze(
        self, 
        prompt: str, 
        context: Dict,
        ) -> List[PromptViolation]:
        """Analyze a prompt and return a list of violations."""
        violations = []
        for rule in self.rules:
            if rule.detector(prompt, context):
                message = rule.message_template.format(**context)
                suggestion = None
                if rule.suggestion_template:
                    suggestion = rule.suggestion_template.format(**context)
                
                violations.append(PromptViolation(
                    rule_name=rule.name,
                    severity=rule.severity,
                    message=message,
                    suggestion=suggestion
                ))
        return violations