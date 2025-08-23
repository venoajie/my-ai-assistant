# src/ai_assistant/prompt_analyzer.py
from dataclasses import dataclass
from typing import List, Optional, Dict, Callable
import re
import yaml
from pathlib import Path

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

    def __init__(
        self, 
        rules_file: Path,
        ):
        self.rules = self._load_rules(rules_file)

    def _load_rules(
        self,
        rules_file: Path,
        ) -> List[AnalysisRule]:
        """Load analysis rules from YAML configuration."""
        with open(rules_file) as f:
            config = yaml.safe_load(f)
        
        rules = []
        for rule_config in config.get('prompt_analysis_rules', []):
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
        """Create a detector function from configuration."""
        detector_type = detector_config.get('type')

        if detector_type == 'multi_file_modification':
            return lambda prompt, ctx: (
                ctx.get('file_count', 0) > detector_config.get('threshold', 1) and
                any(word in prompt.lower() for word in detector_config.get('keywords', []))
            )
        
        elif detector_type == 'multi_file_action':
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