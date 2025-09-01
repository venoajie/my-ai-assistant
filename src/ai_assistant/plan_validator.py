# src/ai_assistant/plan_validator.py
from typing import Dict, Any, Optional, Tuple

from .data_models import ExecutionPlan
from .governance import GOVERNANCE_RULES

# Load the rules from the already-parsed constant.
COMPLIANCE_RULES = GOVERNANCE_RULES.get("plan_compliance_rules", [])

def generate_plan_expectation(prompt: str) -> Optional[Dict[str, Any]]:
    """Analyzes a prompt and returns the expected plan signature if a rule is triggered."""
    prompt_lower = prompt.lower()
    for rule in COMPLIANCE_RULES:
        if any(keyword in prompt_lower for keyword in rule.get("trigger_keywords", [])):
            return rule.get("expected_signature")
    return None # No specific rule triggered

def check_plan_compliance(
    plan: ExecutionPlan, 
    expectation: Dict[str, Any],
    ) -> Tuple[bool, str]:
    """Validates a generated plan against an expected signature."""
    if not expectation:
        return (True, "") # No expectation, so any plan is compliant.

    # Check 1: Step Count
    max_steps = expectation.get("max_steps")
    if max_steps is not None and len(plan) > max_steps:
        return (False, f"Plan has {len(plan)} steps, but the expected maximum is {max_steps}.")

    # Check 2: Allowed Tools
    allowed_tools = expectation.get("allowed_tools")
    if allowed_tools:
        for step in plan:
            tool_name = step.tool_name
            if tool_name not in allowed_tools:
                return (False, f"Plan used a forbidden tool '{tool_name}'. Allowed tools are: {allowed_tools}.")
    
    return (True, "Plan is compliant with the expected signature.")
