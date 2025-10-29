"""
Configuration for Emperion Knowledge Base MCP Server
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
        "postgresql://n8n:n8n_secure_password_change_me@localhost:5432/emperion_knowledge_base"
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
    
    # Emperion specific paths (para referência)
    EMPERION_REPOS: dict[str, str] = {
        "azure-iac": "/emperion/azure-iac",
        "IntakeAPI": "/emperion/IntakeAPI",
        "WebPortals": "/emperion/WebPortals",
        "DevOps": "/emperion/DevOps",
        "AutomatedTests": "/emperion/AutomatedTests",
        "pipelines-templates": "/emperion/pipelines-templates",
        "devops-scripts": "/emperion/devops-scripts",
        "notes": "/emperion/notes",
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
