# src/ai_assistant/data_models.py
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, RootModel, model_validator

from .tools import TOOL_REGISTRY

class PlanStepCondition(BaseModel):
    """Defines a condition for a plan step's execution."""
    from_step: int = Field(..., description="The step number whose output is being checked.")
    # Use Literal for strict validation of the condition type
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
        if tool_name and tool_name.lower() != "null" and not TOOL_REGISTRY.get_tool(tool_name):
            raise ValueError(f"Tool '{tool_name}' is not a valid, registered tool.")
        return self

class ExecutionPlan(RootModel):
    """The root model for an execution plan, which is a list of steps."""
    root: List[PlanStep]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]
    
    def __len__(self):
        return len(self.root)