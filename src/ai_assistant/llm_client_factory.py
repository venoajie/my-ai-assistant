# src/ai_assistant/llm_client_factory.py
import os
import instructor
from openai import AsyncOpenAI
import google.generativeai as genai

from .config import ai_settings
from .response_handler import ResponseHandler # Still needed for provider mapping

def get_instructor_client(model_name: str):
    """
    Factory function to get an instructor-patched client for a given model name.
    This centralizes client creation logic.
    """
    provider_info = ResponseHandler().model_to_provider_map.get(model_name)
    if not provider_info:
        raise ValueError(f"Model '{model_name}' not found in any provider config.")
    
    provider_name = provider_info["provider_name"]
    provider_config = provider_info["config"]

    if provider_name == "gemini":
        api_key = os.getenv(provider_config.api_key_env)
        if not api_key:
            raise ValueError(f"API key env var '{provider_config.api_key_env}' is not set.")
        
        # Configure the underlying Gemini client
        genai.configure(api_key=api_key)
        
        return instructor.from_gemini(
            client=genai.GenerativeModel(model_name=model_name),
            mode=instructor.Mode.GEMINI_JSON,
        )
    elif provider_name == "deepseek":
        return instructor.from_openai(
            client=AsyncOpenAI(
                api_key=os.getenv(provider_config.api_key_env),
                base_url=provider_config.api_endpoint,
            )
        )
    else:
        raise NotImplementedError(f"Instructor client not implemented for provider: '{provider_name}'")