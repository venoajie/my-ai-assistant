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
        
        self.client = get_instructor_client(planning_model_name)
        
        # --- MODIFIED: Correctly determine the provider name for logging ---
        self.provider_name = "unknown"
        for provider, config in ai_settings.providers.items():
            if planning_model_name in config.models:
                self.provider_name = provider
                break


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
            # REFACTORED: This single, standardized call now works for all 
            # OpenAI-compatible providers, removing the need for special "gemini" logic.
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
            
            # --- REFACTORED: Robustly extract raw LLM output ---
            raw_llm_output = None
            # The `instructor` library attaches the original response to the exception
            if hasattr(e, 'body') and e.body and 'choices' in e.body:
                try:
                    raw_llm_output = e.body['choices'][0]['message']['content']
                    logger.debug("Successfully extracted raw response from exception body.")
                except (KeyError, IndexError):
                    logger.debug("Could not find raw response in exception body structure.")

            # Fallback to brittle string parsing only if the robust method fails
            if not raw_llm_output:
                logger.warning("Could not extract raw response from exception body. Falling back to brittle string parsing.")
                try:
                    # This is fragile and should be avoided.
                    raw_llm_output = str(e).split("Invalid JSON:")[1].split("[type=json_invalid")[0].strip()
                except IndexError:
                    logger.error("Failed to parse raw output from exception string. Cannot self-correct.")
                    return None, {"duration": 0, "tokens": {}}

            if ai_settings.general.enable_llm_json_corrector:
                logger.info("Attempting to self-correct invalid JSON with a corrector model.")
                try:
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