#!/usr/bin/env python3
"""
Emperion Knowledge Base - Remote MCP Server with FastMCP
Streamable HTTP transport for DigitalOcean App Platform
"""

import logging
import os
from typing import List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse
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

mcp = FastMCP(
    name="emperion-knowledge-base",
    description="AI-powered code intelligence MCP server"
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
    key_elements: List[str] = [],
    dependencies: List[str] = [],
    tags: List[str] = [],
    file_metadata: Dict[str, Any] = {}
) -> dict:
    """Index a single file's structured knowledge."""
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
    """Index multiple files."""
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
    """Search files."""
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
    """Get file context."""
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
    """Find related files."""
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
def search_by_type(file_type: str, repo: str = None, limit: int = 50) -> dict:
    """Search by file type."""
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
    """Get statistics."""
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
    """Analyze dependencies."""
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


# ==================== CUSTOM ROUTES ====================

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request):
    """Health check for DigitalOcean"""
    try:
        stats = db.get_stats()
        return JSONResponse({
            "status": "healthy",
            "server": "emperion-knowledge-base",
            "version": "2.0.5",
            "protocol": "MCP Streamable HTTP",
            "total_files": stats.total_files,
            "database": "connected"
        })
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return JSONResponse({
            "status": "unhealthy",
            "error": str(e)
        }, status_code=500)


# ==================== APP SETUP ====================

# Get the ASGI app from FastMCP (Starlette, not FastAPI)
mcp_app = mcp.http_app(path='/mcp')

# Create FastAPI app with proper lifespan management
@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """Initialize database on startup"""
    logger.info("🚀 Starting Emperion Knowledge Base MCP Server...")
    logger.info("📍 Deployment: DigitalOcean App Platform")
    logger.info("🔌 MCP Protocol: Streamable HTTP")
    
    try:
        db.init_db()
        logger.info("✅ Database initialized")
        
        if config.validate():
            logger.info("✅ Configuration validated")
        else:
            logger.warning("⚠️  Configuration has warnings")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    # Enter FastMCP's lifespan context (CRITICAL!)
    async with mcp_app.lifespan(app):
        logger.info("✅ FastMCP lifespan initialized")
        logger.info("✅ MCP Server ready on Streamable HTTP")
        yield
    
    logger.info("👋 Shutting down...")


# Create FastAPI app with combined lifespan
app = FastAPI(
    title="Emperion Knowledge Base",
    description="AI-powered code intelligence MCP server",
    version="2.0.5",
    lifespan=app_lifespan
)

# Add root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Emperion Knowledge Base",
        "version": "2.0.5",
        "status": "online",
        "protocol": "MCP Streamable HTTP",
        "mcp_endpoint": "/mcp/",
        "health_endpoint": "/health",
        "tools": 8,
        "note": "MCP server using FastMCP with Streamable HTTP transport"
    }


# Mount FastMCP app at root (MCP endpoints will be at /mcp/)
app.mount("/", mcp_app)


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8080))
    
    logger.info("🚀 Starting with uvicorn...")
    logger.info("📡 Transport: Streamable HTTP")
    logger.info(f"🌐 Server: http://0.0.0.0:{port}")
    logger.info(f"🔌 MCP Endpoint: http://0.0.0.0:{port}/mcp/")
    logger.info(f"❤️  Health Check: http://0.0.0.0:{port}/health")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
