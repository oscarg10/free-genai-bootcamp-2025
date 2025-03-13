"""Configuration management for the Song Vocabulary application."""
from pydantic_settings import BaseSettings
from typing import List
import os
from functools import lru_cache

class Settings(BaseSettings):
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Song Vocabulary Extractor"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "API for extracting vocabulary from song lyrics"
    
    # CORS Settings
    DEV_PORTS: str = "3000,3001,3002,5173,5174"
    FRONTEND_URL: str | None = None
    
    # Rate Limiting
    RATE_LIMIT_AGENT: str = "5/minute"
    RATE_LIMIT_THOUGHTS: str = "10/minute"
    
    # Database
    DATABASE_PATH: str = "data/vocab.db"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

settings = get_settings()
