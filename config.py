"""
Configuration for Repository Knowledge Base MCP Server
"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Server configuration"""
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/repo_knowledge_base"
    )
    
    # Security
    SECRET_KEY: str = os.getenv("MCP_SECRET_KEY", "change-me-in-production")
    ALLOWED_ORIGINS: list[str] = os.getenv("ALLOWED_ORIGINS", "").split(",")
    
    # Rate limiting
    RATE_LIMIT_PER_HOUR: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "100"))
    
    # Indexing
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    SUPPORTED_FILE_TYPES: list[str] = [
        "bicep", "tf", "yaml", "yml", "json", 
        "cs", "py", "js", "ts", "ps1", "sh",
        "md", "env", "Dockerfile"
    ]
    
    # Example repository paths (customize for your setup)
    EXAMPLE_REPOS: dict[str, str] = {
        "infrastructure": "/your-repos/infrastructure",
        "backend-api": "/your-repos/backend-api",
        "frontend-app": "/your-repos/frontend-app",
        "devops": "/your-repos/devops",
        "tests": "/your-repos/tests",
        "pipelines": "/your-repos/pipelines",
        "scripts": "/your-repos/scripts",
        "docs": "/your-repos/docs",
    }
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        if cls.SECRET_KEY == "change-me-in-production":
            print("⚠️  WARNING: Using default SECRET_KEY!")
            return False
        return True


config = Config()
