#!/usr/bin/env python3
"""
Emperion Knowledge Base - Remote MCP Server (SSE)
"""

import json
import logging
from typing import Any, Sequence
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent

from database import db
from models import FileKnowledge, SearchQuery, FileType, Technology
from config import config

# Setup logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp_server = Server("emperion-knowledge-base")


# ==================== LIFESPAN ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("🚀 Starting Emperion Knowledge Base MCP Server...")
    
    try:
        db.init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    logger.info("✅ MCP Server ready on SSE endpoint /sse")
    yield
    logger.info("👋 Shutting down MCP Server...")


# ==================== FASTAPI APP ====================

app = FastAPI(
    title="Emperion Knowledge Base MCP Server",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== MCP TOOLS DEFINITION ====================

@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available MCP tools"""
    return [
        Tool(
            name="index_file",
            description="Index a single file's structured knowledge",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "repo": {"type": "string"},
                    "file_type": {"type": "string", "enum": [ft.value for ft in FileType]},
                    "technology": {"type": "string", "enum": [t.value for t in Technology]},
                    "summary": {"type": "string"},
                    "content_hash": {"type": "string"},
                    "key_elements": {"type": "array", "items": {"type": "string"}},
                    "dependencies": {"type": "array", "items": {"type": "string"}},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "file_metadata": {"type": "object"}
                },
                "required": ["path", "repo", "file_type", "technology", "summary", "content_hash"]
            }
        ),
        Tool(
            name="index_batch",
            description="Index multiple files at once",
            inputSchema={
                "type": "object",
                "properties": {
                    "files": {"type": "array", "items": {"type": "object"}}
                },
                "required": ["files"]
            }
        ),
        Tool(
            name="search_knowledge",
            description="Search files using keyword/semantic search",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "default": 10}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_file_context",
            description="Get complete context for a specific file",
            inputSchema={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"]
            }
        ),
        Tool(
            name="find_related",
            description="Find files related to a given file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "limit": {"type": "integer", "default": 10}
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="search_by_type",
            description="Get all files of a specific type",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_type": {"type": "string"},
                    "repo": {"type": "string"},
                    "limit": {"type": "integer", "default": 50}
                },
                "required": ["file_type"]
            }
        ),
        Tool(
            name="get_stats",
            description="Get knowledge base statistics",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="analyze_dependencies",
            description="Analyze dependency graph for a file",
            inputSchema={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"]
            }
        )
    ]


@mcp_server.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
    """Handle MCP tool calls"""
    try:
        # Index file
        if name == "index_file":
            fk = FileKnowledge(
                path=arguments["path"],
                repo=arguments["repo"],
                file_type=FileType(arguments["file_type"]),
                technology=Technology(arguments["technology"]),
                summary=arguments["summary"],
                content_hash=arguments["content_hash"],
                key_elements=arguments.get("key_elements", []),
                dependencies=arguments.get("dependencies", []),
                dependents=[],
                tags=arguments.get("tags", []),
                file_metadata=arguments.get("file_metadata", {})
            )
            success = db.index_file(fk)
            return [TextContent(type="text", text=json.dumps({
                "status": "success" if success else "error",
                "path": arguments["path"]
            }))]
        
        # Index batch
        elif name == "index_batch":
            files = [FileKnowledge(
                path=f["path"], repo=f["repo"],
                file_type=FileType(f["file_type"]),
                technology=Technology(f["technology"]),
                summary=f["summary"], content_hash=f["content_hash"],
                key_elements=f.get("key_elements", []),
                dependencies=f.get("dependencies", []), dependents=[],
                tags=f.get("tags", []), file_metadata=f.get("file_metadata", {})
            ) for f in arguments["files"]]
            results = db.index_batch(files)
            return [TextContent(type="text", text=json.dumps(results))]
        
        # Search
        elif name == "search_knowledge":
            query = SearchQuery(query=arguments["query"], limit=arguments.get("limit", 10))
            results = db.search_knowledge(query)
            formatted = [{"path": r.path, "repo": r.repo, "summary": r.summary} for r in results]
            return [TextContent(type="text", text=json.dumps({"results": formatted}))]
        
        # Get file context
        elif name == "get_file_context":
            result = db.get_file_context(arguments["path"])
            if result:
                return [TextContent(type="text", text=json.dumps({
                    "path": result.path, "repo": result.repo,
                    "summary": result.summary, "tags": result.tags
                }))]
            return [TextContent(type="text", text=json.dumps({"error": "not_found"}))]
        
        # Find related
        elif name == "find_related":
            results = db.find_related(arguments["path"], arguments.get("limit", 10))
            formatted = [{"path": r.path, "summary": r.summary} for r in results]
            return [TextContent(type="text", text=json.dumps({"results": formatted}))]
        
        # Search by type
        elif name == "search_by_type":
            results = db.search_by_type(
                arguments["file_type"],
                arguments.get("repo"),
                arguments.get("limit", 50)
            )
            formatted = [{"path": r.path, "summary": r.summary} for r in results]
            return [TextContent(type="text", text=json.dumps({"results": formatted}))]
        
        # Get stats
        elif name == "get_stats":
            stats = db.get_stats()
            return [TextContent(type="text", text=json.dumps({
                "total_files": stats.total_files,
                "files_by_type": stats.files_by_type
            }))]
        
        # Analyze dependencies
        elif name == "analyze_dependencies":
            deps = db.analyze_dependencies(arguments["path"])
            return [TextContent(type="text", text=json.dumps({
                "root": deps.root,
                "dependencies": deps.dependencies,
                "dependents": deps.dependents
            }))]
        
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]
    
    except Exception as e:
        logger.error(f"Tool error: {e}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


# ==================== SSE ENDPOINT ====================

@app.get("/sse")
async def handle_sse(request: Request):
    """SSE endpoint for MCP communication"""
    async with SseServerTransport("/messages") as transport:
        async with transport.connect_sse(request.scope, request.receive, request._send) as streams:
            await mcp_server.run(
                streams[0],
                streams[1],
                mcp_server.create_initialization_options()
            )


@app.post("/messages")
async def handle_messages(request: Request):
    """Handle MCP messages"""
    return JSONResponse({"status": "ok"})


# ==================== REGULAR ENDPOINTS ====================

@app.get("/health")
async def health_check():
    """Health check"""
    try:
        stats = db.get_stats()
        return {"status": "healthy", "total_files": stats.total_files}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "unhealthy", "error": str(e)})


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Emperion Knowledge Base",
        "version": "1.0.0",
        "endpoints": {
            "sse": "/sse",
            "messages": "/messages",
            "health": "/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
