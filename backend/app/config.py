"""Application configuration."""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str
    
    # Slash Golf API
    slash_golf_api_key: str
    slash_golf_api_host: str = "live-golf-data.p.rapidapi.com"
    
    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # Application
    environment: str = "development"
    log_level: str = "INFO"
    api_prefix: str = "/api"
    
    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    
    # Tournament defaults
    default_org_id: str = "1"
    default_tournament_id: str = "475"
    default_year: int = 2024
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS origins string to list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
