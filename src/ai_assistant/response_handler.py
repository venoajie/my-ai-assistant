# src/ai_assistant/response_handler.py
import os
import aiohttp 
from typing import Optional, Dict, Any
import asyncio
import time

from .config import ai_settings
from .context_optimizer import ContextOptimizer

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
        
        """Calls the specified AI model asynchronously with enhanced error handling."""
        if model not in self.model_to_provider_map:
            return {
                "tokens": {"prompt": 0, "response": 0, "total": 0},
                "content": f"❌ ERROR: Model '{model}' is not configured.", 
                "duration": 0, 
                "provider_name": "internal",
                }
        if not prompt or not prompt.strip():
            return "❌ ERROR: Empty prompt provided to call_api."
        if len(prompt) > 250000:
            return f"❌ ERROR: Prompt length exceeds the absolute maximum."


        provider_info = self.model_to_provider_map[model]
        provider_name = provider_info["provider_name"]
        provider_config = provider_info["config"]
        final_gen_config = generation_config or \
            ai_settings.generation_params.synthesis.model_dump()

        start_time = time.monotonic() # --- Start timer before the session ---
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=180.0)) as session:
            for attempt in range(max_retries):
                try:
                    print(f"🤖 Calling {provider_name.capitalize()} API (Model: {model}, T: {final_gen_config.get('temperature')}, Attempt: {attempt + 1}/{max_retries})...", end="", flush=True)

                    content = ""
                    if provider_name == "gemini":
                        content = await self._call_gemini(
                            session, 
                            prompt, 
                            model, 
                            provider_config, 
                            final_gen_config,
                            )
                    elif provider_name == "deepseek":
                        content = await self._call_deepseek(
                            session,
                            prompt, 
                            model, 
                            provider_config, 
                            final_gen_config,
                            )
                    else:
                        content = f"❌ ERROR: No call implementation for provider '{provider_name}'."

                    duration = time.monotonic() - start_time # --- Calculate duration ---

                    optimizer = ContextOptimizer()
                    prompt_tokens = optimizer.estimate_tokens(prompt)
                    response_tokens = optimizer.estimate_tokens(content)
                    
                    return {
                        "content": content, 
                        "duration": duration, 
                        "provider_name": provider_name,
                        "tokens": {
                            "prompt": prompt_tokens, 
                            "response": response_tokens, 
                            "total": prompt_tokens + response_tokens,
                            },
                        }

                except (
                    aiohttp.ClientResponseError, 
                    asyncio.TimeoutError, 
                    ValueError,
                    ) as e:
                    
                    if isinstance(e, aiohttp.ClientResponseError) \
                        and 500 <= e.status <= 599:
                        print(f"\n   ...Server error ({e.status}). Retrying...")
                    elif isinstance(e, ValueError) and "empty or whitespace-only" in str(e):
                        print(f"\n   ...API returned empty response. Retrying...")
                    else:
                        # This is now for non-5xx HTTP errors or other unexpected ValueErrors
                        error_msg = f"❌ ERROR: Non-retriable API error for model {model}: {e}"
                        print()
                        # Return empty metrics on failure
                        return {
                            "content": error_msg, 
                            "duration": time.monotonic() - start_time, 
                            "provider_name": provider_name,
                            }
                except Exception as e:
                    # Catch-all for any other unexpected errors
                    error_msg = f"❌ ERROR: An unexpected error occurred during API call for model {model}: {e}"
                    print()
                    # Return empty metrics on failure
                    return {
                        "content": error_msg,
                        "duration": time.monotonic() - start_time, 
                        "provider_name": provider_name,
                        }

                if attempt < max_retries - 1:
                    wait_time = 2 ** (attempt + 1)
                    print(f"   ...Waiting {wait_time}s before retrying.")
                    await asyncio.sleep(wait_time)

        final_error_msg = f"❌ ERROR: API call for model {model} failed after {max_retries} attempts."
        print()
        # Return empty metrics on failure
        return {
            "content": final_error_msg, 
            "duration": time.monotonic() - start_time, 
            "provider_name": provider_name,
            }

    async def _call_gemini(
        self, 
        session: aiohttp.ClientSession, 
        prompt: str, model: str, 
        config: Any, 
        gen_config: Dict,
        ) -> str:
        
        api_key = os.getenv(config.api_key_env)
        if not api_key:
            raise APIKeyNotFoundError(f"API key '{config.api_key_env}' not found.")
                
        api_url = config.api_endpoint_template.format(model=model, api_key=api_key)
        headers = {"Content-Type": "application/json"}
        request_body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": gen_config,
            }
        
        async with session.post(api_url, headers=headers, json=request_body) as response:
            response.raise_for_status()
            response_data = await response.json()
        
        content = response_data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        
        if not content or not content.strip():
            raise ValueError("API returned an empty or whitespace-only response.")

        print(f" ✅ Done!")
        return content

    async def _call_deepseek(
        self, 
        session: aiohttp.ClientSession, 
        prompt: str, model: str, 
        config: Any, 
        gen_config: Dict,
        ) -> str:
        
        api_key = os.getenv(config.api_key_env)
        if not api_key:
            raise APIKeyNotFoundError(f"API key '{config.api_key_env}' not found.")
        
        api_url = config.api_endpoint
        headers = {
            "Content-Type": "application/json", 
            "Authorization": f"Bearer {api_key}",
            }
        request_body = {
            "model": model,
            "messages": [
                {"role": "user", 
                 "content": prompt
                 }
                ], 
            "stream": False, 
            **gen_config,
            }

        async with session.post(api_url, headers=headers, json=request_body) as response:
            response.raise_for_status()
            response_data = await response.json()
        
        content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")

        if not content or not content.strip():
            raise ValueError("API returned an empty or whitespace-only response.")
        
        print(f" ✅ Done!")
        return content