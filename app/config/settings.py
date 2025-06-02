import os
from typing import List, Optional, Dict, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Enhanced application configuration with comprehensive settings."""
    
    # Application Settings
    app_name: str = Field(default="EmailBot", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    reload: bool = Field(default=False, env="RELOAD")
    
    # Database Configuration
    database_url: str = Field(..., env="DATABASE_URL")
    database_pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    database_pool_timeout: int = Field(default=30, env="DATABASE_POOL_TIMEOUT")
    database_pool_recycle: int = Field(default=3600, env="DATABASE_POOL_RECYCLE")
    
    # Redis Configuration
    redis_url: str = Field(..., env="REDIS_URL")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_max_connections: int = Field(default=10, env="REDIS_MAX_CONNECTIONS")
    redis_socket_timeout: int = Field(default=5, env="REDIS_SOCKET_TIMEOUT")
    redis_socket_connect_timeout: int = Field(default=5, env="REDIS_SOCKET_CONNECT_TIMEOUT")
    
    # Microsoft 365 Configuration
    m365_tenant_id: str = Field(..., env="EMAILBOT_M365_TENANT_ID")
    m365_client_id: str = Field(..., env="EMAILBOT_M365_CLIENT_ID")
    m365_client_secret: str = Field(..., env="EMAILBOT_M365_CLIENT_SECRET")
    target_mailbox: str = Field(..., env="EMAILBOT_TARGET_MAILBOX")
    m365_authority: Optional[str] = Field(default=None, env="EMAILBOT_M365_AUTHORITY")
    m365_scope: str = Field(default="https://graph.microsoft.com/.default", env="EMAILBOT_M365_SCOPE")
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    openai_temperature: float = Field(default=0.1, env="OPENAI_TEMPERATURE")
    openai_max_tokens: int = Field(default=300, env="OPENAI_MAX_TOKENS")
    openai_request_timeout: int = Field(default=30, env="OPENAI_REQUEST_TIMEOUT")
    openai_max_retries: int = Field(default=3, env="OPENAI_MAX_RETRIES")
    
    # Email Processing Configuration
    polling_interval_minutes: int = Field(default=5, env="POLLING_INTERVAL_MINUTES")
    batch_size: int = Field(default=10, env="BATCH_SIZE")
    max_processing_time_minutes: int = Field(default=30, env="MAX_PROCESSING_TIME_MINUTES")
    retry_attempts: int = Field(default=3, env="RETRY_ATTEMPTS")
    retry_delay_seconds: int = Field(default=60, env="RETRY_DELAY_SECONDS")
    
    # Confidence Thresholds
    confidence_threshold_auto: float = Field(default=85.0, env="CONFIDENCE_THRESHOLD_AUTO")
    confidence_threshold_suggest: float = Field(default=60.0, env="CONFIDENCE_THRESHOLD_SUGGEST")
    confidence_threshold_review: float = Field(default=40.0, env="CONFIDENCE_THRESHOLD_REVIEW")
    
    # Security Configuration
    encryption_key: str = Field(..., env="ENCRYPTION_KEY")
    token_cache_ttl: int = Field(default=3600, env="TOKEN_CACHE_TTL")
    max_failed_auth_attempts: int = Field(default=5, env="MAX_FAILED_AUTH_ATTEMPTS")
    auth_lockout_duration: int = Field(default=900, env="AUTH_LOCKOUT_DURATION")
    
    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        env="CORS_ALLOW_METHODS"
    )
    cors_allow_headers: List[str] = Field(default=["*"], env="CORS_ALLOW_HEADERS")
    
    # Monitoring Configuration
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    health_check_interval: int = Field(default=60, env="HEALTH_CHECK_INTERVAL")
    
    # Teams Integration Configuration
    teams_webhook_url: Optional[str] = Field(default=None, env="TEAMS_WEBHOOK_URL")
    teams_default_members: List[str] = Field(
        default=["admin@zgcompanies.com"],
        env="TEAMS_DEFAULT_MEMBERS"
    )
    
    # Rate Limiting Configuration
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")
    
    # File and Storage Configuration
    max_email_body_length: int = Field(default=50000, env="MAX_EMAIL_BODY_LENGTH")
    max_attachment_size_mb: int = Field(default=25, env="MAX_ATTACHMENT_SIZE_MB")
    temp_file_cleanup_hours: int = Field(default=24, env="TEMP_FILE_CLEANUP_HOURS")
    
    # Logging Configuration
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    log_file_path: str = Field(default="logs/emailbot.log", env="LOG_FILE_PATH")
    log_max_size_mb: int = Field(default=100, env="LOG_MAX_SIZE_MB")
    log_backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    @field_validator("cors_allow_methods", mode="before")
    @classmethod
    def parse_cors_methods(cls, v):
        """Parse CORS methods from string or list."""
        if isinstance(v, str):
            return [method.strip() for method in v.split(",") if method.strip()]
        return v
    
    @field_validator("cors_allow_headers", mode="before")
    @classmethod
    def parse_cors_headers(cls, v):
        """Parse CORS headers from string or list."""
        if isinstance(v, str):
            return [header.strip() for header in v.split(",") if header.strip()]
        return v
    
    @field_validator("teams_default_members", mode="before")
    @classmethod
    def parse_teams_members(cls, v):
        """Parse Teams default members from string or list."""
        if isinstance(v, str):
            return [member.strip() for member in v.split(",")]
        return v
    
    @field_validator("confidence_threshold_auto")
    @classmethod
    def validate_auto_threshold(cls, v):
        """Validate auto threshold is reasonable."""
        if not 70.0 <= v <= 100.0:
            raise ValueError("Auto threshold must be between 70 and 100")
        return v
    
    class Config:
        env_file = ["test_local.env", "test.env", ".env"]
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration dictionary."""
        return {
            "url": self.database_url,
            "pool_size": self.database_pool_size,
            "max_overflow": self.database_max_overflow,
            "pool_timeout": self.database_pool_timeout,
            "pool_recycle": self.database_pool_recycle
        }
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration dictionary."""
        return {
            "url": self.redis_url,
            "password": self.redis_password,
            "max_connections": self.redis_max_connections,
            "socket_timeout": self.redis_socket_timeout,
            "socket_connect_timeout": self.redis_socket_connect_timeout
        }
    
    def get_openai_config(self) -> Dict[str, Any]:
        """Get OpenAI configuration dictionary."""
        return {
            "api_key": self.openai_api_key,
            "model": self.openai_model,
            "temperature": self.openai_temperature,
            "max_tokens": self.openai_max_tokens,
            "request_timeout": self.openai_request_timeout,
            "max_retries": self.openai_max_retries
        }
    
    def get_confidence_thresholds(self) -> Dict[str, float]:
        """Get confidence threshold configuration."""
        return {
            "auto_handle": self.confidence_threshold_auto,
            "suggest_response": self.confidence_threshold_suggest,
            "human_review": self.confidence_threshold_review,
            "escalate_immediate": 0.0
        }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings() 