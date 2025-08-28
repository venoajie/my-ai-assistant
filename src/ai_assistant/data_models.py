# src/ai_assistant/data_models.py
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, model_validator

from .tools import TOOL_REGISTRY

VALID_WORKFLOW_TOOLS = [
    "execute_refactoring_workflow",
]

class PlanStepCondition(BaseModel):
    """Defines a condition for a plan step's execution."""
    from_step: int = Field(..., description="The step number whose output is being checked.")
    in_output: Optional[str] = Field(None, description="The step runs if this string is in the previous step's output.")
    not_in_output: Optional[str] = Field(None, description="The step runs if this string is NOT in the previous step's output.")

    @model_validator(mode='after')
    def check_one_condition_is_set(self) -> 'PlanStepCondition':
        if self.in_output is None and self.not_in_output is None:
            raise ValueError("Either 'in_output' or 'not_in_output' must be set.")
        if self.in_output is not None and self.not_in_output is not None:
            raise ValueError("Only one of 'in_output' or 'not_in_output' can be set.")
        return self

class PlanStep(BaseModel):
    """Represents a single step in an execution plan."""
    thought: str = Field(..., description="The AI's rationale for this step.")
    tool_name: str = Field(..., description="The name of the tool to execute.")
    args: Dict[str, Any] = Field(default_factory=dict, description="The arguments for the tool.")
    condition: Optional[PlanStepCondition] = None

    @model_validator(mode='after')
    def validate_tool_exists(self) -> 'PlanStep':
        tool_name = self.tool_name
        # --- The validator accepts real tools OR valid workflow tools ---
        is_real_tool = TOOL_REGISTRY.get_tool(tool_name) is not None
        is_workflow_tool = tool_name in VALID_WORKFLOW_TOOLS
        
        if tool_name and tool_name.lower() != "null" and not (is_real_tool or is_workflow_tool):
            raise ValueError(f"Tool '{tool_name}' is not a valid, registered tool.")
        return self


class CritiqueResponse(BaseModel):
    """A structured response from the Adversarial Critic."""
    critique: str = Field(..., description="The concise, bulleted list of findings from the critic. If the plan is sound, this will state that clearly.")
    
    
class ExecutionPlan(BaseModel):
    """The root model for an execution plan, which is a list of steps."""
    steps: List[PlanStep] = Field(..., description="A list of sequential steps to execute.")

    @model_validator(mode='before')
    @classmethod
    def handle_llm_edge_cases(cls, data: Any) -> Any:
        """
        Handles two common LLM mistakes:
        1. Returning a single dictionary for a single-step plan.
        2. Returning a raw list instead of a dictionary with a 'steps' key.
        """
        if isinstance(data, list):
            return {"steps": data}
        
        if isinstance(data, dict) and "steps" not in data:
            return {"steps": [data]}
            
        return data

    def __iter__(self):
        return iter(self.steps)

    def __getitem__(self, item):
        return self.steps[item]
    
    def __len__(self):
        return len(self.steps)
