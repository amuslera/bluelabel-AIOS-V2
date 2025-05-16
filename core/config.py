import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

# Load environment variables
load_dotenv()

class DatabaseConfig(BaseModel):
    """Database configuration"""
    url: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/bluelabel_aios")


class RedisConfig(BaseModel):
    """Redis configuration"""
    host: str = os.getenv("REDIS_HOST", "localhost")
    port: int = int(os.getenv("REDIS_PORT", 6379))
    db: int = int(os.getenv("REDIS_DB", 0))


class LLMConfig(BaseModel):
    """LLM provider configuration"""
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    default_provider: str = "openai"  # openai, anthropic, ollama


class VectorDBConfig(BaseModel):
    """Vector database configuration"""
    host: str = os.getenv("CHROMADB_HOST", "localhost")
    port: int = int(os.getenv("CHROMADB_PORT", 8000))


class EmailConfig(BaseModel):
    """Email gateway configuration"""
    host: str = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    port: int = int(os.getenv("EMAIL_PORT", 587))
    username: str = os.getenv("EMAIL_USERNAME", "")
    password: str = os.getenv("EMAIL_PASSWORD", "")
    use_tls: bool = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"


class WhatsAppConfig(BaseModel):
    """WhatsApp gateway configuration"""
    api_token: str = os.getenv("WHATSAPP_API_TOKEN", "")
    phone_number_id: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")


class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: str = os.getenv("LOG_LEVEL", "INFO")
    file: str = os.getenv("LOG_FILE", "logs/bluelabel_aios.log")


class Settings(BaseModel):
    """Main application configuration with backward compatibility"""
    debug: bool = os.getenv("API_DEBUG", "false").lower() == "true"
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    llm: LLMConfig = LLMConfig()
    vector_db: VectorDBConfig = VectorDBConfig()
    email: EmailConfig = EmailConfig()
    whatsapp: WhatsAppConfig = WhatsAppConfig()
    logging: LoggingConfig = LoggingConfig()
    
    # Add direct access to common settings for compatibility
    @property
    def OPENAI_API_KEY(self) -> Optional[str]:
        return self.llm.openai_api_key
    
    @property
    def ANTHROPIC_API_KEY(self) -> Optional[str]:
        return self.llm.anthropic_api_key
    
    @property
    def DEFAULT_LLM_PROVIDER(self) -> str:
        return self.llm.default_provider
    
    @property
    def DATABASE_URL(self) -> str:
        return self.database.url
    
    @property
    def REDIS_SIMULATION_MODE(self) -> bool:
        return os.getenv("REDIS_SIMULATION_MODE", "true").lower() == "true"
    
    @property
    def LLM_ENABLED(self) -> bool:
        return os.getenv("LLM_ENABLED", "false").lower() == "true"
    
    @property
    def OPENAI_API_KEY(self) -> Optional[str]:
        return self.llm.openai_api_key
    
    @property
    def GOOGLE_GENERATIVEAI_API_KEY(self) -> Optional[str]:
        return os.getenv("GOOGLE_GENERATIVEAI_API_KEY")
    
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.redis.host}:{self.redis.port}/{self.redis.db}"
    
    @property
    def MAX_FILE_SIZE_MB(self) -> int:
        return int(os.getenv("MAX_FILE_SIZE_MB", "100"))
    
    @property
    def JWT_SECRET_KEY(self) -> str:
        return os.getenv("JWT_SECRET_KEY", "insecure-development-key-change-in-production")


# Create global config instances
config = Settings()
settings = config  # Alias for compatibility with architecture.md

def get_settings() -> Settings:
    """Get the global settings instance"""
    return settings
