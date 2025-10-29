"""
Data models for Emperion Knowledge Base
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class FileType(str, Enum):
    """Supported file types"""
    BICEP = "bicep"
    TERRAFORM = "terraform"
    HELM = "helm"
    YAML = "yaml"
    CSHARP = "csharp"
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    POWERSHELL = "powershell"
    BASH = "bash"
    MARKDOWN = "markdown"
    DOCKERFILE = "dockerfile"
    ENV = "env"
    JSON = "json"


class Technology(str, Enum):
    """Technology categories"""
    INFRASTRUCTURE = "infrastructure-as-code"
    BACKEND = "backend"
    FRONTEND = "frontend"
    DEVOPS = "devops"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    CONFIG = "configuration"


class FileKnowledge(BaseModel):
    """Main knowledge structure for a file"""
    
    # Pydantic V2: Use ConfigDict instead of Config class
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "path": "/emperion/azure-iac/main.bicep",
                "repo": "azure-iac",
                "file_type": "bicep",
                "technology": "infrastructure-as-code",
                "summary": "Main infrastructure definition for Azure resources",
                "key_elements": [
                    "storageAccount",
                    "appServicePlan",
                    "keyVault"
                ],
                "dependencies": [
                    "/emperion/azure-iac/modules/storage.bicep",
                    "/emperion/azure-iac/modules/keyvault.bicep"
                ],
                "dependents": [],
                "tags": ["azure", "infrastructure", "production"],
                "content_hash": "abc123def456",
                "indexed_at": "2025-10-29T18:00:00Z",
                "file_metadata": {
                    "line_count": 150,
                    "complexity": "medium",
                    "last_modified": "2025-10-28"
                }
            }
        }
    )
    
    # Identity
    path: str = Field(..., description="Full path to the file")
    repo: str = Field(..., description="Repository name")
    file_type: FileType = Field(..., description="Type of file")
    technology: Technology = Field(..., description="Technology category")
    
    # Content
    summary: str = Field(..., description="Brief summary of the file purpose")
    key_elements: List[str] = Field(
        default_factory=list,
        description="Important elements (resources, classes, functions)"
    )
    
    # Relationships
    dependencies: List[str] = Field(
        default_factory=list,
        description="Files this one depends on"
    )
    dependents: List[str] = Field(
        default_factory=list,
        description="Files that depend on this one"
    )
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    content_hash: str = Field(..., description="Hash of the content for change detection")
    indexed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Additional context
    file_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extra metadata (line_count, complexity, etc)"
    )


class BatchIndexRequest(BaseModel):
    """Request to index multiple files at once"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "files": [
                    {
                        "path": "/emperion/azure-iac/main.bicep",
                        "repo": "azure-iac",
                        "file_type": "bicep",
                        "technology": "infrastructure-as-code",
                        "summary": "Main infrastructure",
                        "key_elements": ["storage", "keyvault"],
                        "dependencies": [],
                        "dependents": [],
                        "tags": ["azure"],
                        "content_hash": "abc123",
                        "file_metadata": {}
                    }
                ]
            }
        }
    )
    
    files: List[FileKnowledge] = Field(..., description="List of files to index")


class SearchQuery(BaseModel):
    """Search query parameters"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "azure storage configuration",
                "file_types": ["bicep"],
                "technologies": ["infrastructure-as-code"],
                "repos": ["azure-iac"],
                "tags": ["production"],
                "limit": 10
            }
        }
    )
    
    query: str = Field(..., description="Search query")
    file_types: Optional[List[FileType]] = Field(None, description="Filter by file types")
    technologies: Optional[List[Technology]] = Field(None, description="Filter by technology")
    repos: Optional[List[str]] = Field(None, description="Filter by repositories")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    limit: int = Field(10, description="Maximum number of results", ge=1, le=100)


class SearchResult(BaseModel):
    """Search result item"""
    file: FileKnowledge
    relevance_score: float = Field(..., description="Relevance score (0-1)")
    matched_elements: List[str] = Field(
        default_factory=list,
        description="Elements that matched the query"
    )


class DependencyGraph(BaseModel):
    """Dependency graph for a component"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "root": "/emperion/IntakeAPI/Services/AuthService.cs",
                "dependencies": [
                    "/emperion/IntakeAPI/Models/User.cs",
                    "/emperion/IntakeAPI/Interfaces/IAuthService.cs"
                ],
                "dependents": [
                    "/emperion/IntakeAPI/Controllers/AuthController.cs"
                ],
                "depth": 2
            }
        }
    )
    
    root: str = Field(..., description="Root file path")
    dependencies: List[str] = Field(..., description="Direct dependencies")
    dependents: List[str] = Field(..., description="Direct dependents")
    depth: int = Field(..., description="Depth of dependency tree")


class IndexStats(BaseModel):
    """Statistics about the indexed knowledge"""
    total_files: int
    files_by_type: Dict[str, int]
    files_by_repo: Dict[str, int]
    files_by_technology: Dict[str, int]
    last_indexed: Optional[datetime]
    total_dependencies: int
