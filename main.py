#!/usr/bin/env python3
"""
Emperion Knowledge Base - Remote MCP Server (SSE)

This MCP server stores and serves structured knowledge about Emperion repositories.
It works in conjunction with a local filesystem MCP server, where Claude acts as
the orchestrator between reading local files and storing extracted knowledge remotely.

Workflow:
1. Claude uses filesystem MCP to read local files
2. Claude extracts and structures knowledge
3. Claude uses this MCP server (via SSE) to store the knowledge
4. Later, Claude queries this server for context when helping with development
"""

import json
import logging
from typing import Any
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.fastmcp import FastMCP

from database import db
from models import (
    FileKnowledge, BatchIndexRequest, SearchQuery,
    SearchResult, FileType, Technology
)
from config import config

# Setup logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("emperion-knowledge-base")


# ==================== LIFESPAN ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting Emperion Knowledge Base MCP Server...")
    logger.info(f"📊 Database: {config.DATABASE_URL[:50]}...")
    
    try:
        db.init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    if not config.validate():
        logger.warning("⚠️  Running with default configuration!")
    
    logger.info("✅ MCP Server ready on SSE endpoint /sse")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down MCP Server...")


# ==================== FASTAPI APP ====================

app = FastAPI(
    title="Emperion Knowledge Base MCP Server",
    description="Remote MCP server for storing and querying code knowledge",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS if config.ALLOWED_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== MCP TOOLS ====================

@mcp.tool()
def index_file(
    path: str,
    repo: str,
    file_type: str,
    technology: str,
    summary: str,
    content_hash: str,
    key_elements: list[str] = [],
    dependencies: list[str] = [],
    tags: list[str] = [],
    file_metadata: dict = {}
) -> str:
    """
    Index a single file's structured knowledge.
    Claude should extract key information from files read via filesystem MCP
    and store it here for future reference.
    
    Args:
        path: Full path to the file (e.g., /emperion/azure-iac/main.bicep)
        repo: Repository name (e.g., azure-iac, IntakeAPI)
        file_type: Type of file (bicep, csharp, python, yaml, etc.)
        technology: Technology category (infrastructure, backend, frontend, etc.)
        summary: Brief summary of file purpose (1-2 sentences)
        content_hash: Hash of content for change detection
        key_elements: Important elements (resources, classes, functions, etc.)
        dependencies: Files this one depends on (full paths)
        tags: Searchable tags (e.g., azure, production, api)
        file_metadata: Additional metadata (line_count, complexity, etc.)
    """
    try:
        file_knowledge = FileKnowledge(
            path=path,
            repo=repo,
            file_type=FileType(file_type),
            technology=Technology(technology),
            summary=summary,
            key_elements=key_elements,
            dependencies=dependencies,
            dependents=[],
            tags=tags,
            content_hash=content_hash,
            file_metadata=file_metadata
        )
        
        success = db.index_file(file_knowledge)
        
        return json.dumps({
            "status": "success" if success else "error",
            "message": f"{'Successfully indexed' if success else 'Failed to index'} {path}",
            "path": path
        }, indent=2)
    except Exception as e:
        logger.error(f"Error in index_file: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        }, indent=2)


@mcp.tool()
def index_batch(files: list[dict]) -> str:
    """
    Index multiple files at once for efficiency.
    
    Args:
        files: List of file objects with same structure as index_file
    """
    try:
        file_objects = []
        for file_data in files:
            file_objects.append(FileKnowledge(
                path=file_data["path"],
                repo=file_data["repo"],
                file_type=FileType(file_data["file_type"]),
                technology=Technology(file_data["technology"]),
                summary=file_data["summary"],
                key_elements=file_data.get("key_elements", []),
                dependencies=file_data.get("dependencies", []),
                dependents=[],
                tags=file_data.get("tags", []),
                content_hash=file_data["content_hash"],
                file_metadata=file_data.get("file_metadata", {})
            ))
        
        results = db.index_batch(file_objects)
        
        return json.dumps({
            "status": "success",
            "results": results,
            "message": f"Indexed {results['success']} files, {results['failed']} failed"
        }, indent=2)
    except Exception as e:
        logger.error(f"Error in index_batch: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        }, indent=2)


@mcp.tool()
def search_knowledge(
    query: str,
    file_types: list[str] = [],
    technologies: list[str] = [],
    repos: list[str] = [],
    tags: list[str] = [],
    limit: int = 10
) -> str:
    """
    Search for files using semantic/keyword search.
    Searches through summaries, key elements, and tags.
    
    Args:
        query: Search query (e.g., 'azure storage configuration')
        file_types: Filter by file types
        technologies: Filter by technology categories
        repos: Filter by repositories
        tags: Filter by tags
        limit: Maximum results to return (1-100)
    """
    try:
        search_query = SearchQuery(
            query=query,
            file_types=[FileType(ft) for ft in file_types],
            technologies=[Technology(t) for t in technologies],
            repos=repos if repos else None,
            tags=tags if tags else None,
            limit=min(limit, 100)
        )
        
        results = db.search_knowledge(search_query)
        
        formatted = []
        for result in results:
            formatted.append({
                "path": result.path,
                "repo": result.repo,
                "file_type": result.file_type,
                "technology": result.technology,
                "summary": result.summary,
                "key_elements": result.key_elements,
                "tags": result.tags,
                "dependencies": result.dependencies,
                "file_metadata": result.file_metadata
            })
        
        return json.dumps({
            "status": "success",
            "count": len(formatted),
            "results": formatted
        }, indent=2)
    except Exception as e:
        logger.error(f"Error in search_knowledge: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        }, indent=2)


@mcp.tool()
def get_file_context(path: str) -> str:
    """
    Get complete context for a specific file by its path.
    
    Args:
        path: Full path to the file
    """
    try:
        result = db.get_file_context(path)
        
        if result:
            return json.dumps({
                "status": "success",
                "file": {
                    "path": result.path,
                    "repo": result.repo,
                    "file_type": result.file_type,
                    "technology": result.technology,
                    "summary": result.summary,
                    "key_elements": result.key_elements,
                    "dependencies": result.dependencies,
                    "dependents": result.dependents,
                    "tags": result.tags,
                    "indexed_at": result.indexed_at.isoformat(),
                    "file_metadata": result.file_metadata
                }
            }, indent=2)
        else:
            return json.dumps({
                "status": "not_found",
                "message": f"File not found: {path}"
            }, indent=2)
    except Exception as e:
        logger.error(f"Error in get_file_context: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        }, indent=2)


@mcp.tool()
def find_related(path: str, limit: int = 10) -> str:
    """
    Find files related to a given file (same repo, similar technology).
    
    Args:
        path: Path to the reference file
        limit: Maximum results
    """
    try:
        results = db.find_related(path, limit)
        
        formatted = [
            {
                "path": r.path,
                "repo": r.repo,
                "file_type": r.file_type,
                "summary": r.summary,
                "tags": r.tags
            }
            for r in results
        ]
        
        return json.dumps({
            "status": "success",
            "count": len(formatted),
            "related_files": formatted
        }, indent=2)
    except Exception as e:
        logger.error(f"Error in find_related: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        }, indent=2)


@mcp.tool()
def search_by_type(file_type: str, repo: str = None, limit: int = 50) -> str:
    """
    Get all files of a specific type, optionally filtered by repo.
    
    Args:
        file_type: File type to search for
        repo: Optional: filter by repository
        limit: Maximum results
    """
    try:
        results = db.search_by_type(file_type, repo, limit)
        
        formatted = [
            {
                "path": r.path,
                "repo": r.repo,
                "summary": r.summary,
                "tags": r.tags
            }
            for r in results
        ]
        
        return json.dumps({
            "status": "success",
            "file_type": file_type,
            "count": len(formatted),
            "files": formatted
        }, indent=2)
    except Exception as e:
        logger.error(f"Error in search_by_type: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        }, indent=2)


@mcp.tool()
def get_stats() -> str:
    """Get statistics about the indexed knowledge base."""
    try:
        stats = db.get_stats()
        
        return json.dumps({
            "status": "success",
            "stats": {
                "total_files": stats.total_files,
                "files_by_type": stats.files_by_type,
                "files_by_repo": stats.files_by_repo,
                "files_by_technology": stats.files_by_technology,
                "last_indexed": stats.last_indexed.isoformat() if stats.last_indexed else None,
                "total_dependencies": stats.total_dependencies
            }
        }, indent=2)
    except Exception as e:
        logger.error(f"Error in get_stats: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        }, indent=2)


@mcp.tool()
def analyze_dependencies(path: str) -> str:
    """
    Analyze dependency graph for a specific file.
    
    Args:
        path: Path to analyze
    """
    try:
        deps = db.analyze_dependencies(path)
        
        return json.dumps({
            "status": "success",
            "dependency_graph": {
                "root": deps.root,
                "dependencies": deps.dependencies,
                "dependents": deps.dependents,
                "depth": deps.depth
            }
        }, indent=2)
    except Exception as e:
        logger.error(f"Error in analyze_dependencies: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        }, indent=2)


# ==================== MOUNT MCP TO FASTAPI ====================

# Mount the MCP SSE endpoint to FastAPI
app.mount("/", mcp.sse_app())


# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    """Health check endpoint for DigitalOcean"""
    try:
        # Test database connection
        stats = db.get_stats()
        return {
            "status": "healthy",
            "database": "connected",
            "total_files": stats.total_files
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Emperion Knowledge Base MCP Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "sse": "/sse",
            "messages": "/messages/",
            "health": "/health"
        }
    }


# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
