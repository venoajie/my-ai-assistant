# src/ai_assistant/response_handler.py
import os
import time
from typing import Optional, Dict, Any

from .config import ai_settings
from .llm_client_factory import get_instructor_client
from .utils.context_optimizer import ContextOptimizer

class APIKeyNotFoundError(Exception):
    """Custom exception for missing API keys."""
    pass

class ResponseHandler:
    def __init__(self):
        """Initializes the ResponseHandler using settings from the config file."""
        self.model_to_provider_map = {}
        for provider_name, provider_config in ai_settings.providers.items():
            for model_name in provider_config.models:
                self.model_to_provider_map[model_name] = {
                    "provider_name": provider_name,
                    "config": provider_config,
                }

    def check_api_keys(self):
        """Checks that API keys for all configured models are present."""
        required_keys = set(provider.api_key_env for provider in ai_settings.providers.values())
        for key_env in required_keys:
            if not os.getenv(key_env):
                raise APIKeyNotFoundError(f"Required API key env var '{key_env}' is not set.")

    async def call_api(
        self, 
        prompt: str, 
        model: str, 
        generation_config: Optional[Dict[str, Any]] = None, 
        max_retries: int = 3,
        ) -> Dict[str, Any]:
        """
        Calls the specified AI model asynchronously using the central client factory.
        """
        start_time = time.monotonic()
        
        if model not in self.model_to_provider_map:
            # ... (error handling for model not found)
            return {"content": f"❌ ERROR: Model '{model}' is not configured.", "duration": 0, "tokens": {}}

        provider_info = self.model_to_provider_map[model]
        provider_name = provider_info["provider_name"]
        
        try:
            # --- THE FIX: Use the central, unified client factory ---
            client = get_instructor_client(model)
            
            final_gen_config = generation_config or ai_settings.generation_params.synthesis.model_dump(exclude_none=True)
            
            print(f"🤖 Calling {provider_name.capitalize()} API (Model: {model}, T: {final_gen_config.get('temperature')}, Retries: {max_retries})...", end="", flush=True)

            # Use the standard .chat.completions.create method
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_retries=max_retries,
                **final_gen_config,
            )
            
            content = response.choices[0].message.content
            if not content or not content.strip():
                raise ValueError("API returned an empty or whitespace-only response.")

            print(" ✅ Done!")
            
            optimizer = ContextOptimizer()
            prompt_tokens = optimizer.estimate_tokens(prompt)
            response_tokens = optimizer.estimate_tokens(content)
            
            return {
                "content": content, 
                "duration": time.monotonic() - start_time, 
                "provider_name": provider_name,
                "tokens": {"prompt": prompt_tokens, "response": response_tokens, "total": prompt_tokens + response_tokens},
            }
        except Exception as e:
            error_msg = f"API call for model {model} failed. Reason: {e}"
            print(f"\n   ...❌ ERROR: {error_msg}")
            return {"content": f"❌ ERROR: {error_msg}", "duration": time.monotonic() - start_time, "tokens": {}}