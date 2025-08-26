# src/ai_assistant/planner.py
import structlog
from typing import List, Dict, Any, Optional, Tuple
import json
from pydantic import ValidationError

from .prompt_builder import PromptBuilder
from .tools import TOOL_REGISTRY
from .config import ai_settings
from .data_models import ExecutionPlan
from .llm_client_factory import get_instructor_client
from .response_handler import ResponseHandler

logger = structlog.get_logger(__name__)

class Planner:
    def __init__(self):
        """
        Initializes the Planner by getting a pre-configured, instructor-patched
        client from the central factory.
        """
        self.prompt_builder = PromptBuilder()
        planning_model_name = ai_settings.model_selection.planning
        
        # The constructor's ONLY job is to get the client from the factory.
        self.client = get_instructor_client(planning_model_name)
        
        # We get the provider name directly from the client for logging.
        # The client.provider attribute might be a string or an enum, so we convert to string.
        self.provider_name = str(self.client.provider)

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
            # we check if the lowercase provider string CONTAINS "gemini".
            # This correctly handles 'Provider.GEMINI' and 'gemini'.
            if "gemini" in self.provider_name.lower():
                plan = await self.client.create(
                    response_model=ExecutionPlan,
                    messages=[{"role": "user", "content": prompt}],
                    generation_config=planning_gen_config
                )
            else: # Assumes OpenAI-compatible (like DeepSeek)
                plan = await self.client.chat.completions.create(
                    model=planning_model_name,
                    response_model=ExecutionPlan,
                    messages=[{"role": "user", "content": prompt}],
                    max_retries=2,
                    **planning_gen_config,
                )

            logger.info("Plan generated and validated successfully.", step_count=len(plan))
            return plan, {"duration": 0, "tokens": {}}

        except ValidationError as e:
            logger.warning("Initial plan generation failed Pydantic validation.", error=str(e))
            if ai_settings.general.enable_llm_json_corrector:
                logger.info("Attempting to self-correct invalid JSON with a corrector model.")
                try:
                    # Extract the raw, broken JSON string from the exception
                    # This is a bit of a hack, but it's how we get the source material
                    raw_llm_output = str(e).split("Invalid JSON:")[1].split("[type=json_invalid")[0].strip()

                    correction_prompt = f"""The following JSON is broken. Please fix it. Return ONLY the corrected JSON, with no other text or explanation.

BROKEN JSON:
```json
{raw_llm_output}
```

CORRECTED JSON:"""
                    
                    handler = ResponseHandler()
                    corrector_model = ai_settings.model_selection.json_corrector
                    correction_result = await handler.call_api(correction_prompt, model=corrector_model, generation_config={"temperature": 0.0})
                    corrected_json_str = correction_result["content"].strip().replace("```json", "").replace("```", "").strip()
                    
                    plan = ExecutionPlan.model_validate_json(corrected_json_str)
                    logger.info("Successfully self-corrected and validated the plan.", step_count=len(plan))
                    return plan, {"duration": 0, "tokens": {}}
                except Exception as correction_error:
                    logger.error("JSON self-correction failed.", error=str(correction_error))
                    return None, {"duration": 0, "tokens": {}}
            
            return None, {"duration": 0, "tokens": {}} # Return None if corrector is disabled or fails
        
        except Exception as e:
             logger.error("Failed to generate a valid plan with instructor.", error=str(e))
             return None, {"duration": 0, "tokens": {}}