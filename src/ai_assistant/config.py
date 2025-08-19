# src/ai_assistant/config.py
import yaml
from pathlib import Path
from typing import Dict, Optional, List
from pydantic import BaseModel, Field
from importlib import resources

# --- Pydantic Models for Type-Safe Configuration ---
class ModelSelectionConfig(BaseModel):
    planning: str
    synthesis: str
    critique: str
    json_corrector: str
    
class GeneralConfig(BaseModel):
    personas_directory: str
    sessions_directory: str
    max_file_size_mb: int
    universal_base_persona: Optional[str] = None
    auto_inject_files: List[str] = Field(default_factory=list)
    critique_persona_alias: str
    failure_persona_alias: str
    local_plugins_directory: str = ".ai/plugins"
    enable_llm_json_corrector: bool = Field(default=True) # Let's default to True

class ContextOptimizerConfig(BaseModel):
    max_tokens: int
    prompt_compression_threshold: int = Field(
        default=0, 
        description="Token count above which to use compact prompts. 0 to disable.",
        )

class GitToolConfig(BaseModel):
    branch_prefix: str

class ToolsConfig(BaseModel):
    git: GitToolConfig

class DeepSeekDiscountConfig(BaseModel):
    start_hour: int
    start_minute: int
    end_hour: int
    end_minute: int

class GenerationParams(BaseModel):
    temperature: float
    topP: Optional[float] = None
    topK: Optional[int] = None

class GenerationConfig(BaseModel):
    planning: GenerationParams
    synthesis: GenerationParams
    critique: GenerationParams

class ProviderConfig(BaseModel):
    api_key_env: str
    models: List[str]
    api_endpoint: Optional[str] = None
    api_endpoint_template: Optional[str] = None

class AIConfig(BaseModel):
    config_version: str
    model_selection: ModelSelectionConfig
    default_provider: str
    general: GeneralConfig
    context_optimizer: ContextOptimizerConfig
    tools: ToolsConfig
    deepseek_discount: DeepSeekDiscountConfig
    generation_params: GenerationConfig
    providers: Dict[str, ProviderConfig]


# --- Configuration Loading Logic
def load_ai_settings() -> AIConfig:
    """Loads and merges config from package defaults, user config, and project config"""
    # 1. Load package defaults using the correct resource loading mechanism
    try:
        default_config_text = resources.files('ai_assistant').joinpath('default_config.yml').read_text(encoding='utf-8')
        config_data = yaml.safe_load(default_config_text)
    except (FileNotFoundError, yaml.YAMLError) as e:
        print(f"FATAL: Could not load or parse the default package configuration. Error: {e}")
        # This is a fatal error, as the application cannot run without its base config.
        exit(1)
    
    # 2. Load user config overrides
    user_config_path = Path.home() / ".config" / "ai_assistant" / "config.yml"
    if user_config_path.exists():
        with open(user_config_path, 'r') as f:
            user_config = yaml.safe_load(f)
        # --- FIX: Only merge if the loaded config is not empty ---
        if user_config:
            config_data = deep_merge(
                config_data, 
                user_config,
                )
    
    # 3. Load project config overrides
    project_config_path = Path.cwd() / ".ai_config.yml"
    if project_config_path.exists():
        with open(project_config_path, 'r') as f:
            project_config = yaml.safe_load(f)
        # --- FIX: Only merge if the loaded config is not empty ---
        if project_config:
            config_data = deep_merge(
                config_data, 
                project_config,
                )
    
    return AIConfig.model_validate(config_data)

def deep_merge(base: Dict, update: Dict) -> Dict:
    """Deep merge two dictionaries"""
    # --- FIX: Add a guard clause for safety ---
    if not isinstance(update, dict):
        return base
        
    for key, value in update.items():
        if isinstance(value, dict) \
            and key in base \
                and isinstance(base[key], dict):
            base[key] = deep_merge(
                base[key], 
                value,
                )
        else:
            base[key] = value
    return base

# --- Global Singleton Instance ---
ai_settings = load_ai_settings()