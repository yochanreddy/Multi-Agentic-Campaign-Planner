from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

class Config(BaseSettings):
    """Configuration settings for the creative planner."""
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_DEBUG: bool = False
    
    # Storage Settings
    STORAGE_PATH: str = "storage"
    IMAGE_PATH: str = "images"
    
    # LLM Settings
    LLM_MODEL: str = "gpt-4"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2000
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = "logs/creative_planner.log"
    
    # Project Settings
    project_root: Optional[str] = None
    openai_api_key: Optional[str] = None
    seed: int = 42  # Random seed for reproducibility
    
    # Database Settings
    pgsql_host: Optional[str] = None
    pgsql_database_name: Optional[str] = None
    pgsql_username: Optional[str] = None
    pgsql_password: Optional[str] = None
    
    # API Endpoints
    ideogram_overlay_url: Optional[str] = None
    ideogram_generate_url: Optional[str] = None
    flux_api_host_post: Optional[str] = None
    flux_api_host_get: Optional[str] = None
    alison_analyze_endpoint: Optional[str] = None
    
    # API Keys
    nyx_bfl_flux_key: Optional[str] = None
    ideogram_key: Optional[str] = None
    
    # GCP Settings
    gcp_type: Optional[str] = None
    gcp_project_id: Optional[str] = None
    gcp_pri_key_id: Optional[str] = None
    gcp_pri_key: Optional[str] = None
    gcp_client_email: Optional[str] = None
    gcp_client_id: Optional[str] = None
    gcp_auth_uri: Optional[str] = None
    gcp_token_uri: Optional[str] = None
    gcp_auth_provider: Optional[str] = None
    gcp_client_cert_url: Optional[str] = None
    gcp_universe_domain: Optional[str] = None
    brand_gcp_bucket_name: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  # Allow extra fields from env
    
    def get_storage_path(self) -> Path:
        """Get the absolute path to the storage directory."""
        return Path(self.STORAGE_PATH)
    
    def get_image_path(self) -> Path:
        """Get the absolute path to the images directory."""
        return self.get_storage_path() / self.IMAGE_PATH
    
    def get_log_file(self) -> Optional[Path]:
        """Get the absolute path to the log file."""
        if self.LOG_FILE:
            return Path(self.LOG_FILE)
        return None

# Create a global config instance
config = Config() 