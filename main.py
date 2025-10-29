#!/usr/bin/env python3
"""
Emperion Knowledge Base - Remote MCP Server with FastMCP
Streamable HTTP transport for Claude Desktop
"""

import logging
from typing import List, Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastmcp import FastMCP

from database import db
from models import (
    FileKnowledge, SearchQuery, FileType, Technology,
    DependencyGraph, IndexStats
)
from config import config

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== FASTMCP SERVER ====================

# Create FastMCP server WITHOUT deprecated parameters
mcp = FastMCP("emperion-knowledge-base")


# ==================== MCP TOOLS ====================

@mcp.tool()
def index_file(
    path: str,
    repo: str,
    file_type: str,
    technology: str,
    summary: str,
    content_hash: str,
    key_elements: List[str] = [],
    dependencies: List[str] = [],
    tags: List[str] = [],
    file_metadata: Dict[str, Any] = {}
) -> dict:
    """
    Index a single file's structured knowledge.
    
    Args:
        path: Full path to the file
        repo: Repository name
        file_type: Type of file (bicep, csharp, python, etc.)
        technology: Technology category (infrastructure-as-code, backend, etc.)
        summary: Brief summary of the file purpose
        content_hash: Hash of the content for change detection
        key_elements: Important elements (resources, classes, functions)
        dependencies: Files this one depends on
        tags: Searchable tags
        file_metadata: Extra metadata (line_count, complexity, etc)
    
    Returns:
        dict: Status and indexed file path
    """
    try:
        fk = FileKnowledge(
            path=path,
            repo=repo,
            file_type=FileType(file_type),
            technology=Technology(technology),
            summary=summary,
            content_hash=content_hash,
            key_elements=key_elements,
            dependencies=dependencies,
            dependents=[],
            tags=tags,
            file_metadata=file_metadata
        )
        success = db.index_file(fk)
        
        if success:
            logger.info(f"✅ Indexed: {path}")
            return {"status": "success", "path": path}
        else:
            logger.error(f"❌ Failed to index: {path}")
            return {"status": "error", "path": path, "message": "Database operation failed"}
            
    except ValueError as e:
        logger.error(f"❌ Invalid input for {path}: {e}")
        return {"status": "error", "path": path, "message": str(e)}
    except Exception as e:
        logger.error(f"❌ Unexpected error indexing {path}: {e}")
        return {"status": "error", "path": path, "message": f"Unexpected error: {str(e)}"}


@mcp.tool()
def index_batch(files: List[Dict[str, Any]]) -> dict:
    """
    Index multiple files at once for efficient bulk operations.
    
    Args:
        files: List of file objects with all required fields
    
    Returns:
        dict: Success and failed counts
    """
    try:
        file_objects = []
        for f in files:
            fk = FileKnowledge(
                path=f["path"],
                repo=f["repo"],
                file_type=FileType(f["file_type"]),
                technology=Technology(f["technology"]),
                summary=f["summary"],
                content_hash=f["content_hash"],
                key_elements=f.get("key_elements", []),
                dependencies=f.get("dependencies", []),
                dependents=[],
                tags=f.get("tags", []),
                file_metadata=f.get("file_metadata", {})
            )
            file_objects.append(fk)
        
        results = db.index_batch(file_objects)
        logger.info(f"📦 Batch indexed: {results['success']} success, {results['failed']} failed")
        return results
        
    except Exception as e:
        logger.error(f"❌ Batch index error: {e}")
        return {"success": 0, "failed": len(files), "error": str(e)}


@mcp.tool()
def search_knowledge(
    query: str,
    limit: int = 10,
    file_types: List[str] = None,
    technologies: List[str] = None,
    repos: List[str] = None,
    tags: List[str] = None
) -> dict:
    """
    Search files using keyword/semantic search across summaries, tags, and key elements.
    
    Args:
        query: Search query string
        limit: Maximum number of results (1-100)
        file_types: Filter by file types (optional)
        technologies: Filter by technology categories (optional)
        repos: Filter by repository names (optional)
        tags: Filter by tags (optional)
    
    Returns:
        dict: Search results with path, repo, and summary
    """
    try:
        search_query = SearchQuery(
            query=query,
            limit=min(limit, 100),
            file_types=[FileType(ft) for ft in file_types] if file_types else None,
            technologies=[Technology(t) for t in technologies] if technologies else None,
            repos=repos,
            tags=tags
        )
        
        results = db.search_knowledge(search_query)
        formatted = [
            {
                "path": r.path,
                "repo": r.repo,
                "file_type": r.file_type,
                "technology": r.technology,
                "summary": r.summary,
                "tags": r.tags,
                "key_elements": r.key_elements
            }
            for r in results
        ]
        
        logger.info(f"🔍 Search '{query}' returned {len(formatted)} results")
        return {"results": formatted, "count": len(formatted)}
        
    except Exception as e:
        logger.error(f"❌ Search error: {e}")
        return {"results": [], "count": 0, "error": str(e)}


@mcp.tool()
def get_file_context(path: str) -> dict:
    """
    Get complete context for a specific file including all metadata.
    
    Args:
        path: Full path to the file
    
    Returns:
        dict: Complete file information or error
    """
    try:
        result = db.get_file_context(path)
        
        if result:
            logger.info(f"📄 Retrieved context for: {path}")
            return {
                "path": result.path,
                "repo": result.repo,
                "file_type": result.file_type,
                "technology": result.technology,
                "summary": result.summary,
                "key_elements": result.key_elements,
                "dependencies": result.dependencies,
                "dependents": result.dependents,
                "tags": result.tags,
                "content_hash": result.content_hash,
                "indexed_at": result.indexed_at.isoformat(),
                "file_metadata": result.file_metadata
            }
        else:
            logger.warning(f"⚠️  File not found: {path}")
            return {"error": "not_found", "path": path}
            
    except Exception as e:
        logger.error(f"❌ Error getting context for {path}: {e}")
        return {"error": str(e), "path": path}


@mcp.tool()
def find_related(path: str, limit: int = 10) -> dict:
    """
    Find files related to a given file based on repo, technology, and tags.
    
    Args:
        path: Full path to the source file
        limit: Maximum number of related files (1-50)
    
    Returns:
        dict: List of related files with paths and summaries
    """
    try:
        results = db.find_related(path, min(limit, 50))
        formatted = [
            {
                "path": r.path,
                "repo": r.repo,
                "file_type": r.file_type,
                "technology": r.technology,
                "summary": r.summary,
                "tags": r.tags
            }
            for r in results
        ]
        
        logger.info(f"🔗 Found {len(formatted)} related files for: {path}")
        return {"results": formatted, "count": len(formatted)}
        
    except Exception as e:
        logger.error(f"❌ Error finding related files for {path}: {e}")
        return {"results": [], "count": 0, "error": str(e)}


@mcp.tool()
def search_by_type(
    file_type: str,
    repo: str = None,
    limit: int = 50
) -> dict:
    """
    Get all files of a specific type, optionally filtered by repository.
    
    Args:
        file_type: Type of file (bicep, csharp, python, yaml, etc.)
        repo: Repository name (optional)
        limit: Maximum number of results (1-100)
    
    Returns:
        dict: List of files matching the type
    """
    try:
        results = db.search_by_type(file_type, repo, min(limit, 100))
        formatted = [
            {
                "path": r.path,
                "repo": r.repo,
                "summary": r.summary,
                "technology": r.technology,
                "tags": r.tags,
                "indexed_at": r.indexed_at.isoformat()
            }
            for r in results
        ]
        
        logger.info(f"📁 Found {len(formatted)} files of type '{file_type}'")
        return {"results": formatted, "count": len(formatted)}
        
    except Exception as e:
        logger.error(f"❌ Error searching by type '{file_type}': {e}")
        return {"results": [], "count": 0, "error": str(e)}


@mcp.tool()
def get_stats() -> dict:
    """
    Get knowledge base statistics including totals by type, repo, and technology.
    
    Returns:
        dict: Comprehensive statistics about the indexed knowledge
    """
    try:
        stats = db.get_stats()
        result = {
            "total_files": stats.total_files,
            "files_by_type": stats.files_by_type,
            "files_by_repo": stats.files_by_repo,
            "files_by_technology": stats.files_by_technology,
            "total_dependencies": stats.total_dependencies,
            "last_indexed": stats.last_indexed.isoformat() if stats.last_indexed else None
        }
        
        logger.info(f"📊 Stats: {stats.total_files} total files")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error getting stats: {e}")
        return {"error": str(e)}


@mcp.tool()
def analyze_dependencies(path: str) -> dict:
    """
    Analyze dependency graph for a file showing what it depends on and what depends on it.
    
    Args:
        path: Full path to the file
    
    Returns:
        dict: Dependency graph with dependencies and dependents
    """
    try:
        deps = db.analyze_dependencies(path)
        result = {
            "root": deps.root,
            "dependencies": deps.dependencies,
            "dependents": deps.dependents,
            "depth": deps.depth,
            "total_dependencies": len(deps.dependencies),
            "total_dependents": len(deps.dependents)
        }
        
        logger.info(f"🔀 Analyzed dependencies for: {path}")
        return result
        
    except ValueError as e:
        logger.warning(f"⚠️  {e}")
        return {"error": str(e), "path": path}
    except Exception as e:
        logger.error(f"❌ Error analyzing dependencies for {path}: {e}")
        return {"error": str(e), "path": path}


# ==================== FASTAPI APP WITH CUSTOM ENDPOINTS ====================

# Create FastAPI app with custom lifespan
@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """Lifespan for FastAPI app - initialize database on startup"""
    logger.info("🚀 Starting Emperion Knowledge Base MCP Server...")
    try:
        db.init_db()
        logger.info("✅ Database initialized")
        
        # Validate configuration
        if config.validate():
            logger.info("✅ Configuration validated")
        else:
            logger.warning("⚠️  Configuration has warnings (see above)")
        
        # Initialize MCP session manager
        async with mcp.session_manager.run():
            logger.info("✅ MCP Server ready on Streamable HTTP")
            yield  # Server runs here
        
        logger.info("👋 Shutting down MCP Server...")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

app = FastAPI(
    title="Emperion Knowledge Base",
    description="AI-powered code intelligence MCP server",
    version="2.0.0",
    lifespan=app_lifespan
)

# Mount MCP Streamable HTTP endpoint at /mcp
app.mount("/mcp", mcp.streamable_http_app())

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        stats = db.get_stats()
        return {
            "status": "healthy",
            "server": "emperion-knowledge-base",
            "version": "2.0.0",
            "transport": "streamable-http",
            "total_files": stats.total_files,
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with server information"""
    return {
        "name": "Emperion Knowledge Base",
        "version": "2.0.0",
        "description": "AI-powered code intelligence MCP server",
        "transport": "streamable-http",
        "endpoints": {
            "mcp": "/mcp (Streamable HTTP)",
            "health": "/health",
            "docs": "/docs"
        },
        "tools": [
            "index_file",
            "index_batch",
            "search_knowledge",
            "get_file_context",
            "find_related",
            "search_by_type",
            "get_stats",
            "analyze_dependencies"
        ]
    }


# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting Emperion Knowledge Base MCP Server...")
    logger.info("📡 Transport: Streamable HTTP")
    logger.info("🔌 MCP Endpoint: http://0.0.0.0:8000/mcp")
    logger.info("❤️  Health Check: http://0.0.0.0:8000/health")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
