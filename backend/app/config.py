"""Application configuration."""
from pydantic_settings import BaseSettings
from typing import List, Optional


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
    
    # Discord Integration (optional)
    discord_webhook_url: str = "https://discord.com/api/webhooks/1464311605084028931/qPXmTCWouXiB6Ahz6wIZWCJhV0OwlArZh-Qqoaibi8OEow_uS_9bAP-Pgz2atpGnfFHz"
    discord_enabled: bool = False
    discord_invite_url: Optional[str] = None  # Discord server invite link (e.g., https://discord.gg/xxxxx)
    discord_server_id: Optional[str] = None  # Discord server ID for widget (found in Server Settings → Widget)
    
    # Push Notifications (PWA)
    push_notifications_enabled: bool = False
    vapid_public_key: Optional[str] = None
    vapid_private_key: Optional[str] = None
    vapid_email: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS origins string to list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
