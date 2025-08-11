# ai_assistant/response_handler.py
import os
import json
import requests
from typing import Optional, Dict, Any
import time

from .config import ai_settings

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
                    "config": provider_config
                }

    # --- Method for pre-flight checks ---
    def check_api_keys(self):
        """
        Checks that API keys for all configured models are present in the environment.
        Raises APIKeyNotFoundError if any key is missing.
        """
        required_keys = set()
        for provider_config in ai_settings.providers.values():
            required_keys.add(provider_config.api_key_env)
        
        for key_env in required_keys:
            if not os.getenv(key_env):
                raise APIKeyNotFoundError(
                    f"Required API key environment variable '{key_env}' is not set. "
                    "Please set it before running the assistant."
                )

    def call_api(self, prompt: str, model: str, generation_config: Optional[Dict[str, Any]] = None, max_retries: int = 3) -> str:
        """
        Calls the specified AI model with enhanced error handling, validation, and retry logic.
        """
        if model not in self.model_to_provider_map:
            return f"❌ ERROR: Model '{model}' is not configured in ai_assistant_config.yml."

        # --- Input Validation ---
        if not prompt or not prompt.strip():
            return "❌ ERROR: Empty prompt provided to call_api."
        
        # A very generous limit to catch runaway context issues.
        if len(prompt) > 250000:
            return f"❌ ERROR: Prompt length ({len(prompt)}) exceeds the absolute maximum of 250,000 characters."

        provider_info = self.model_to_provider_map[model]
        provider_name = provider_info["provider_name"]
        provider_config = provider_info["config"]
        
        # Use provided generation_config or fall back to the model's default from config
        final_gen_config = generation_config or ai_settings.generation_params.synthesis.model_dump()
        
        for attempt in range(max_retries):
            try:
                print(f"🤖 Calling {provider_name.capitalize()} API (Model: {model}, T: {final_gen_config.get('temperature')}, Attempt: {attempt + 1}/{max_retries})...", end="", flush=True)
                
                if provider_name == "gemini":
                    return self._call_gemini(prompt, model, provider_config, final_gen_config)
                elif provider_name == "deepseek":
                    return self._call_deepseek(prompt, model, provider_config, final_gen_config)
                else:
                    return f"❌ ERROR: No call implementation for provider '{provider_name}'."

            except requests.exceptions.Timeout as e:
                print(f"\n   ...Request timed out: {e}")
            except requests.exceptions.RequestException as e:
                # This catches network errors and server-side errors (5xx)
                status_code = e.response.status_code if e.response is not None else "N/A"
                if isinstance(e.response, requests.Response) and 500 <= status_code <= 599:
                    print(f"\n   ...Server error ({status_code}). Retrying...")
                else:
                    # For client-side errors (4xx) or other non-transient issues, fail immediately.
                    print() # Move to the next line for clean error output
                    return f"❌ ERROR: Non-retriable API request error for model {model}: {e}"
            
            except Exception as e:
                # Catch any other unexpected errors and fail immediately.
                print() # Move to the next line
                return f"❌ ERROR: An unexpected error occurred during API call for model {model}: {e}"

            # If we are not on the last attempt, wait before retrying
            if attempt < max_retries - 1:
                # Exponential backoff: 2s, 4s, 8s...
                wait_time = 2 ** (attempt + 1)
                print(f"   ...Waiting {wait_time}s before retrying.")
                time.sleep(wait_time)

        print() # Move to the next line
        return f"❌ ERROR: API call for model {model} failed after {max_retries} attempts."

    def _call_gemini(self, prompt: str, model: str, config: Any, gen_config: Dict) -> str:
        api_key = os.getenv(config.api_key_env)

        if not api_key:
            raise APIKeyNotFoundError(f"API key '{config.api_key_env}' not found in environment.")
                
        api_url = config.api_endpoint_template.format(model=model, api_key=api_key)
        headers = {"Content-Type": "application/json"}
        request_body = {"contents": [{"parts": [{"text": prompt}]}],"generationConfig": gen_config}
        
        start_time = time.time()
        response = requests.post(api_url, headers=headers, data=json.dumps(request_body), timeout=180)
        duration = time.time() - start_time

        response.raise_for_status() # Will raise an exception for non-2xx status codes
        response_data = response.json()
        
        content = response_data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        
        print(f" ✅ Done! (⏱️ {duration:.2f}s)")
        return content

    def _call_deepseek(self, prompt: str, model: str, config: Any, gen_config: Dict) -> str:
        api_key = os.getenv(config.api_key_env)

        if not api_key:
            raise APIKeyNotFoundError(f"API key '{config.api_key_env}' not found in environment.")
        
        api_url = config.api_endpoint
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        request_body = {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False, **gen_config}

        start_time = time.time()
        response = requests.post(api_url, headers=headers, data=json.dumps(request_body), timeout=180)
        duration = time.time() - start_time

        response.raise_for_status() # Will raise an exception for non-2xx status codes
        response_data = response.json()
        
        content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")

        print(f" ✅ Done! (⏱️ {duration:.2f}s)")
        return content