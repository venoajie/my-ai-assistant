# src/ai_assistant/llm_client_factory.py
import os
import instructor
from openai import AsyncOpenAI

from .config import ai_settings

def get_instructor_client(model_name: str):
    """
    Factory function to get an instructor-patched client for a given model name.
    This function now uses the OpenAI-compatible standard for ALL providers.
    """
    provider_info = None
    # --- NEW, MORE ROBUST LOOKUP LOGIC ---
    for provider_name, provider_config in ai_settings.providers.items():
        if model_name in provider_config.models:
            provider_info = {
                "provider_name": provider_name,
                "config": provider_config,
            }
            break # Found it, stop searching

    if not provider_info:
        raise ValueError(f"Model '{model_name}' not found in any provider config.")
    
    provider_config = provider_info["config"]

    api_key = os.getenv(provider_config.api_key_env)
    if not api_key:
        raise ValueError(f"API key env var '{provider_config.api_key_env}' is not set.")

    # This single block now works for both DeepSeek and Gemini
    # --- MODIFIED: Force JSON mode to prevent parallel tool-calling issues ---
    return instructor.from_openai(
        client=AsyncOpenAI(
            api_key=api_key,
            base_url=provider_config.api_endpoint,
        ),
        mode=instructor.Mode.JSON # This is the key change
    )