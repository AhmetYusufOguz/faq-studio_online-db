import logging
from pathlib import Path
from typing import Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings using Pydantic BaseSettings"""
    
    # Embedding & AI Settings
    EMBED_MODEL: str = Field(default="bge-m3", description="Ollama embedding model name")
    OLLAMA_BASE_URL: str = Field(default="http://ollama:11434", description="Ollama server base URL")
    SIM_THRESHOLD: float = Field(default=0.70, ge=0.0, le=1.0, description="Similarity threshold for duplicate detection")
    
    # Database Settings
    DATABASE_URL: str = Field(..., description="PostgreSQL database connection URL")
    
    # File Paths
    JSON_PATH: str = Field(default="/app/data/questions.json", description="JSON backup file path")
    CATEGORIES_PATH: str = Field(default="/app/data/categories.json", description="Categories file path")
    CHROMA_DB_PATH: str = Field(default="./chroma_db", description="ChromaDB persistence path")
    
    # Server Settings
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, ge=1, le=65535, description="Server port")
    WORKERS: int = Field(default=1, ge=1, description="Number of worker processes")
    
    # Logging Settings
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(
        default="%(asctime)s %(levelname)s %(name)s :: %(message)s",
        description="Log message format"
    )
    
    # Security & Performance
    CORS_ORIGINS: list[str] = Field(default=["*"], description="CORS allowed origins")
    REQUEST_TIMEOUT: int = Field(default=30, ge=1, description="Request timeout in seconds")
    MAX_EMBEDDING_LENGTH: int = Field(default=1000, ge=1, description="Maximum text length for embedding")
    
    # Optional Development Settings
    DEBUG: bool = Field(default=False, description="Debug mode")
    RELOAD: bool = Field(default=False, description="Auto-reload on code changes")
    
    @validator('LOG_LEVEL')
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'LOG_LEVEL must be one of: {valid_levels}')
        return v.upper()
    
    @validator('DATABASE_URL')
    def validate_database_url(cls, v):
        """Basic validation for database URL"""
        if not v:
            raise ValueError('DATABASE_URL is required')
        if not v.startswith(('postgresql://', 'postgres://')):
            raise ValueError('DATABASE_URL must be a PostgreSQL connection string')
        return v
    
    @validator('OLLAMA_BASE_URL')
    def validate_ollama_url(cls, v):
        """Validate Ollama URL format"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('OLLAMA_BASE_URL must start with http:// or https://')
        return v.rstrip('/')  # Remove trailing slash
    
    @validator('JSON_PATH', 'CATEGORIES_PATH', 'CHROMA_DB_PATH')
    def create_parent_dirs(cls, v):
        """Ensure parent directories exist"""
        path = Path(v)
        if not path.name:  # If it's a directory path
            path.mkdir(parents=True, exist_ok=True)
        else:  # If it's a file path
            path.parent.mkdir(parents=True, exist_ok=True)
        return str(path)
    
    def get_log_level_int(self) -> int:
        """Get logging level as integer"""
        return getattr(logging, self.LOG_LEVEL)
    
    def get_database_config(self) -> dict:
        """Extract database connection parameters"""
        # Simple parsing - you might want to use a proper URL parser
        import urllib.parse
        parsed = urllib.parse.urlparse(self.DATABASE_URL)
        return {
            'host': parsed.hostname,
            'port': parsed.port,
            'user': parsed.username,
            'password': parsed.password,
            'database': parsed.path.lstrip('/'),
        }
    
    class Config:
        # Look for .env file in current directory and parent directories
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        
        # Allow extra fields in case you want to add custom settings
        extra = "ignore"
        
        # Environment variable prefix (optional)
        # env_prefix = "FAQ_"
        
        # Enable JSON schema generation
        schema_extra = {
            "example": {
                "EMBED_MODEL": "bge-m3",
                "OLLAMA_BASE_URL": "http://localhost:11434",
                "SIM_THRESHOLD": 0.70,
                "DATABASE_URL": "postgresql://user:pass@localhost:5432/faqdb",
                "JSON_PATH": "/app/data/questions.json",
                "CATEGORIES_PATH": "/app/data/categories.json",
                "CHROMA_DB_PATH": "./chroma_db",
                "HOST": "0.0.0.0",
                "PORT": 8000,
                "LOG_LEVEL": "INFO",
                "DEBUG": False
            }
        }


# Global settings instance
settings = Settings()


# Convenience function for backward compatibility
def get_settings() -> Settings:
    """Get application settings instance"""
    return settings


# Development helper
def print_config():
    """Print current configuration (excluding sensitive data)"""
    config_dict = settings.dict()
    
    # Mask sensitive fields
    sensitive_fields = ['DATABASE_URL']
    for field in sensitive_fields:
        if field in config_dict and config_dict[field]:
            config_dict[field] = config_dict[field][:10] + "***"
    
    print("Current Configuration:")
    for key, value in config_dict.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    # Test configuration loading
    print_config()