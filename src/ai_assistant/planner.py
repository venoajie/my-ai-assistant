# src/ai_assistant/planner.py
import os
import instructor
import structlog
from openai import AsyncOpenAI
import google.generativeai as genai
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
        
        planning_model_name = ai_settings.model_selection.planning
        provider_info = ResponseHandler().model_to_provider_map.get(planning_model_name)
        if not provider_info:
            raise ValueError(f"Planning model '{planning_model_name}' not found in any provider config.")
        
        self.provider_name = provider_info["provider_name"]
        provider_config = provider_info["config"]

        if self.provider_name == "gemini":
            api_key = os.getenv(provider_config.api_key_env)
            if not api_key:
                raise ValueError(f"API key env var '{provider_config.api_key_env}' is not set.")
            
            self.client = instructor.from_gemini(
                client=genai.GenerativeModel(model_name=planning_model_name),
                mode=instructor.Mode.GEMINI_JSON,
            )
        elif self.provider_name == "deepseek":
            self.client = instructor.from_openai(
                client=AsyncOpenAI(
                    api_key=os.getenv(provider_config.api_key_env),
                    base_url=provider_config.api_endpoint,
                )
            )
        else:
            raise NotImplementedError(f"Planning is not implemented for provider: '{self.provider_name}'")

    async def create_plan(
        self,
        query: str,
        history: List[Dict[str, Any]] = None,
        persona_content: Optional[str] = None,
        use_compact_protocol: bool = False,
        is_output_mode: bool = False,
        plan_expectation: Optional[Dict[str, Any]] = None, 
        ) -> Tuple[Optional[ExecutionPlan], Dict[str, Any]]:
        
        logger.info("Generating execution plan with structured output...", provider=self.provider_name)
        prompt = self.prompt_builder.build_planning_prompt(
            query,
            TOOL_REGISTRY.get_tool_descriptions(),
            history,
            persona_content,
            use_compact_protocol=use_compact_protocol,
            is_output_mode=is_output_mode,
            plan_expectation=plan_expectation, 
        )
        
        planning_model_name = ai_settings.model_selection.planning
        planning_gen_config = ai_settings.generation_params.planning.model_dump(exclude_none=True)

        try:
            if self.provider_name == "gemini":
                plan = await self.client.create(
                    response_model=ExecutionPlan,
                    messages=[{"role": "user", "content": prompt}],
                    # Pass the plain dictionary, not a GenerationConfig object.
                    generation_config=planning_gen_config
                )
            else: # Assumes OpenAI-compatible (DeepSeek)
                plan = await self.client.chat.completions.create(
                    model=planning_model_name,
                    response_model=ExecutionPlan,
                    messages=[{"role": "user", "content": prompt}],
                    max_retries=2,
                    **planning_gen_config,
                )

            logger.info("Plan generated and validated successfully.", step_count=len(plan))
            return plan, {"duration": 0, "tokens": {}}

        except Exception as e:
            logger.error("Failed to generate a valid plan with instructor.", error=str(e))
            return None, {"duration": 0, "tokens": {}}