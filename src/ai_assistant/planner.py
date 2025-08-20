# src/ai_assistant/planner.py
import os
import instructor
import structlog
from openai import AsyncOpenAI
from typing import List, Dict, Any, Optional, Tuple

from .prompt_builder import PromptBuilder
from .response_handler import ResponseHandler
from .tools import TOOL_REGISTRY
from .config import ai_settings
from .data_models import ExecutionPlan

logger = structlog.get_logger(__name__)

class Planner:
    def __init__(self):
        self.prompt_builder = PromptBuilder()
        # Get the provider config for the planning model
        planning_model = ai_settings.model_selection.planning
        provider_info = ResponseHandler().model_to_provider_map.get(planning_model)
        if not provider_info:
            raise ValueError(f"Planning model '{planning_model}' not found in any provider config.")
        
        provider_config = provider_info["config"]
        
        # Create an instructor-patched client.
        # This works for any OpenAI-compatible API, like DeepSeek.
        self.client = instructor.patch(
            AsyncOpenAI(
                api_key=os.getenv(provider_config.api_key_env),
                base_url=provider_config.api_endpoint,
            ),
            mode=instructor.Mode.JSON,
        )

    async def create_plan(
        self,
        query: str,
        history: List[Dict[str, Any]] = None,
        persona_content: Optional[str] = None,
        use_compact_protocol: bool = False,
        is_output_mode: bool = False,
        ) -> Tuple[Optional[ExecutionPlan], Dict[str, Any]]:
        
        logger.info("Generating execution plan with structured output...")
        tool_descriptions = TOOL_REGISTRY.get_tool_descriptions()
        prompt = self.prompt_builder.build_planning_prompt(
            query,
            tool_descriptions,
            history,
            persona_content,
            use_compact_protocol=use_compact_protocol,
            is_output_mode=is_output_mode,
        )
        
        planning_model = ai_settings.model_selection.planning
        planning_gen_config = ai_settings.generation_params.planning.model_dump(exclude_none=True)

        try:
            plan = await self.client.chat.completions.create(
                model=planning_model,
                response_model=ExecutionPlan,
                messages=[{"role": "user", "content": prompt}],
                max_retries=2,
                **planning_gen_config,
            )
            logger.info("Plan generated and validated successfully.", step_count=len(plan))
            for i, step in enumerate(plan):
                logger.debug(f"  - Step {i+1}: {step.thought} -> {step.tool_name}({step.args})")
            
            # Note: We can't get precise token counts from instructor easily,
            # so we'll return an empty metrics object for now.
            api_result = {"duration": 0, "tokens": {}}
            return plan, api_result

        except Exception as e:
            logger.error("Failed to generate a valid plan with instructor.", error=str(e))
            # Return an empty, valid plan on failure
            return None, {"duration": 0, "tokens": {}}