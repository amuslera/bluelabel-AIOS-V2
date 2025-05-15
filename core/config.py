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


class AppConfig(BaseModel):
    """Main application configuration"""
    debug: bool = os.getenv("API_DEBUG", "false").lower() == "true"
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    llm: LLMConfig = LLMConfig()
    vector_db: VectorDBConfig = VectorDBConfig()
    email: EmailConfig = EmailConfig()
    whatsapp: WhatsAppConfig = WhatsAppConfig()
    logging: LoggingConfig = LoggingConfig()


# Create global config instance
config = AppConfig()
