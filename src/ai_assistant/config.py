# src/ai_assistant/config.py

import os
import yaml
from pathlib import Path
from typing import Dict, Optional, List
from pydantic import BaseModel, Field, model_validator
from importlib import resources
import structlog  

logger = structlog.get_logger(__name__)

# --- Pydantic Models for Type-Safe Configuration ---
class ModelSelectionConfig(BaseModel):
    planning: str
    synthesis: str
    critique: str
    json_corrector: str
    query_expander: str 
    
class PathsConfig(BaseModel):
    """Holds all key resolved paths for the application."""
    project_root: Path
    sessions_dir: Path
    user_personas_dir: Path
    project_local_personas_dir: Path
    local_plugins_dir: Path

class GeneralConfig(BaseModel):
    personas_directory: str
    sessions_directory: str
    max_file_size_mb: int
    universal_base_persona: Optional[str] = None
    auto_inject_files: List[str] = Field(default_factory=list)
    critique_persona_alias: str
    failure_persona_alias: str
    local_plugins_directory: str = ".ai/plugins"
    enable_llm_json_corrector: bool = Field(default=True)
    log_level: str = Field(
        default="INFO", 
        description="Default application log level.",
        )
    services_template_directory: str = Field(
        default="src/services", 
        description="Default path for service templates.",
        )
    service_template_files: List[str] = Field(
        default_factory=lambda: ["Dockerfile", 
                                 "pyproject.toml"],
        )

class ContextOptimizerConfig(BaseModel):
    max_tokens: int
    prompt_compression_threshold: int = Field(
        default=0, 
        description="Token count above which to use compact prompts. 0 to disable.",
        )

class GitToolConfig(BaseModel):
    branch_prefix: str

# --- NEW: Configuration model for the shell tool ---
class ShellToolConfig(BaseModel):
    allowed_commands: List[str] = Field(default_factory=list)

class ToolsConfig(BaseModel):
    git: GitToolConfig
    # --- ADDED: Shell tool config is now part of the main ToolsConfig ---
    shell: ShellToolConfig

class DeepSeekDiscountConfig(BaseModel):
    start_hour: int
    start_minute: int
    end_hour: int
    end_minute: int

class GenerationParams(BaseModel):
    temperature: float
    top_p: Optional[float] = Field(None, alias='topP')
    top_k: Optional[int] = Field(None, alias='topK')
    
class GenerationConfig(BaseModel):
    planning: GenerationParams
    synthesis: GenerationParams
    critique: GenerationParams

class OracleCloudConfig(BaseModel):
    """Configuration for Oracle Cloud Object Storage."""
    namespace: Optional[str] = Field(None, description="OCI namespace")
    bucket: Optional[str] = Field(None, description="OCI bucket name")
    region: Optional[str] = Field(None, description="OCI region")
    enable_caching: bool = Field(True, description="Enable local caching of downloaded indexes")
    cache_ttl_hours: int = Field(24, description="Cache TTL in hours before re-downloading")
    
class RAGConfig(BaseModel):
    """Configuration for the RAG subsystem."""
    embedding_model_name: str = 'BAAI/bge-large-en-v1.5'
    collection_name: str = Field("codebase_collection", description="Default collection name for ChromaDB.")
    chroma_server_host: Optional[str] = Field(None, description="Hostname of the ChromaDB server.")
    chroma_server_port: Optional[int] = Field(None, description="Port of the ChromaDB server.")
    chroma_server_ssl: bool = Field(False, description="Use SSL to connect to the ChromaDB server.")
    
    default_branch: str = Field("main", description="Default branch for RAG indexing if git detection fails.")
    enable_branch_awareness: bool = Field(True, description="Enable branch-specific indexes.")
    
    fallback_embedding_providers: List[str] = Field(
        default_factory=lambda: ["openai"], 
        description="Fallback embedding providers if local model fails",
    )
    
    oracle_cloud: Optional[OracleCloudConfig] = Field(
        default_factory=OracleCloudConfig,
        description="Oracle Cloud Object Storage configuration",
    )
    local_index_path: str = Field(
        ".ai_rag_index", 
        description="Path for the local ChromaDB index, relative to project root.",
        )
    
    # --- SETTINGS FOR RERANKING ---
    enable_reranking: bool = Field(
        False, 
        description="Enable a second-stage reranker for more accurate RAG results."
    )
    reranker_model_name: str = Field(
        'cross-encoder/ms-marco-MiniLM-L-6-v2',
        description="The CrossEncoder model to use for reranking."
    )
    retrieval_n_results: int = Field(
        25,
        description="How many documents to initially retrieve from ChromaDB before reranking."
    )
    rerank_top_n: int = Field(
        5,
        description="How many of the top documents to return after the reranking step."
    )

    # --- NEW: Add the validator to enforce the configuration contract ---
    @model_validator(mode='after')
    def validate_reranking_counts(self) -> 'RAGConfig':
        if self.enable_reranking and self.rerank_top_n > self.retrieval_n_results:
            raise ValueError(
                f"'rerank_top_n' ({self.rerank_top_n}) cannot be greater than "
                f"'retrieval_n_results' ({self.retrieval_n_results})."
            )
        return self



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
    rag: RAGConfig = Field(default_factory=RAGConfig)
    providers: Dict[str, ProviderConfig]
    paths: PathsConfig

# --- Configuration Loading Logic
def load_ai_settings() -> AIConfig:
    """Loads and merges config from package defaults, user config, and project config"""
    try:
        default_config_text = resources.files('ai_assistant').joinpath('default_config.yml').read_text(encoding='utf-8')
        config_data = yaml.safe_load(default_config_text)
        logger.debug("Loaded default package configuration.") 
    except (FileNotFoundError, yaml.YAMLError) as e:
        print(f"FATAL: Could not load or parse the default package configuration. Error: {e}")
        exit(1)
    
    user_config_dir_str = os.getenv('AI_ASSISTANT_CONFIG_DIR', str(Path.home() / ".config" / "ai_assistant"))
    user_config_dir = Path(user_config_dir_str)
    
    user_config_path = user_config_dir / "config.yml"
    if user_config_path.exists():
        with open(user_config_path, 'r') as f:
            user_config = yaml.safe_load(f)
        if user_config:
            config_data = deep_merge(config_data, user_config)
     
    project_config_path = Path.cwd() / ".ai_config.yml"
    if project_config_path.exists():
        with open(project_config_path, 'r') as f:
            project_config = yaml.safe_load(f)
        if project_config:
            logger.info("Applying project-level configuration override.", path=str(project_config_path)) 
            config_data = deep_merge(config_data, project_config)
    
    # 1. First, calculate all runtime paths based on the merged config dictionary.
    project_root = Path.cwd()
    general_config = config_data.get("general", {})
    
    # 2. Create the PathsConfig object manually.
    paths_obj = PathsConfig(
        project_root=project_root,
        sessions_dir=project_root / general_config.get("sessions_directory", ".ai_sessions"),
        user_personas_dir=user_config_dir / general_config.get("personas_directory", "personas"),
        project_local_personas_dir=project_root / ".ai" / "personas",
        local_plugins_dir=project_root / general_config.get("local_plugins_directory", ".ai/plugins"),
    )
    
    # 3. Inject the fully formed PathsConfig object into our main config dictionary.
    config_data["paths"] = paths_obj.model_dump()

    # 4. NOW, with a complete dictionary, ask Pydantic to validate everything at once.
    # This will succeed because the 'paths' field is now present and correctly structured.
    return AIConfig.model_validate(config_data)


def deep_merge(base: Dict, update: Dict) -> Dict:
    """Deep merge two dictionaries"""
    if not isinstance(update, dict):
        return base
        
    for key, value in update.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            base[key] = deep_merge(base[key], value)
        else:
            base[key] = value
    return base

ai_settings = load_ai_settings()