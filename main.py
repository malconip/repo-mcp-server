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

import asyncio
import json
import logging
from typing import Any, Sequence
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)

from database import db
from models import (
    FileKnowledge, BatchIndexRequest, SearchQuery,
    SearchResult, FileType, Technology
)
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

@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools for knowledge management"""
    return [
        # ===== INDEXING TOOLS =====
        Tool(
            name="index_file",
            description=(
                "Index a single file's structured knowledge. "
                "Claude should extract key information from files read via filesystem MCP "
                "and store it here for future reference."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Full path to the file (e.g., /emperion/azure-iac/main.bicep)"
                    },
                    "repo": {
                        "type": "string",
                        "description": "Repository name (e.g., azure-iac, IntakeAPI)"
                    },
                    "file_type": {
                        "type": "string",
                        "enum": [ft.value for ft in FileType],
                        "description": "Type of file"
                    },
                    "technology": {
                        "type": "string",
                        "enum": [t.value for t in Technology],
                        "description": "Technology category"
                    },
                    "summary": {
                        "type": "string",
                        "description": "Brief summary of file purpose (1-2 sentences)"
                    },
                    "key_elements": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Important elements (resources, classes, functions, etc.)"
                    },
                    "dependencies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Files this one depends on (full paths)"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Searchable tags (e.g., azure, production, api)"
                    },
                    "content_hash": {
                        "type": "string",
                        "description": "Hash of content for change detection"
                    },
                    "file_metadata": {
                        "type": "object",
                        "description": "Additional metadata (line_count, complexity, etc.)"
                    }
                },
                "required": ["path", "repo", "file_type", "technology", "summary", "content_hash"]
            }
        ),
        
        Tool(
            name="index_batch",
            description="Index multiple files at once for efficiency",
            inputSchema={
                "type": "object",
                "properties": {
                    "files": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string"},
                                "repo": {"type": "string"},
                                "file_type": {"type": "string"},
                                "technology": {"type": "string"},
                                "summary": {"type": "string"},
                                "key_elements": {"type": "array", "items": {"type": "string"}},
                                "dependencies": {"type": "array", "items": {"type": "string"}},
                                "tags": {"type": "array", "items": {"type": "string"}},
                                "content_hash": {"type": "string"},
                                "file_metadata": {"type": "object"}
                            },
                            "required": ["path", "repo", "file_type", "technology", "summary", "content_hash"]
                        }
                    }
                },
                "required": ["files"]
            }
        ),
        
        # ===== SEARCH TOOLS =====
        Tool(
            name="search_knowledge",
            description=(
                "Search for files using semantic/keyword search. "
                "Searches through summaries, key elements, and tags."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'azure storage configuration')"
                    },
                    "file_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by file types"
                    },
                    "technologies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by technology categories"
                    },
                    "repos": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by repositories"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by tags"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "description": "Maximum results to return (1-100)"
                    }
                },
                "required": ["query"]
            }
        ),
        
        Tool(
            name="get_file_context",
            description="Get complete context for a specific file by its path",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Full path to the file"
                    }
                },
                "required": ["path"]
            }
        ),
        
        Tool(
            name="find_related",
            description="Find files related to a given file (same repo, similar technology)",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the reference file"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "description": "Maximum results"
                    }
                },
                "required": ["path"]
            }
        ),
        
        Tool(
            name="search_by_type",
            description="Get all files of a specific type, optionally filtered by repo",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_type": {
                        "type": "string",
                        "enum": [ft.value for ft in FileType],
                        "description": "File type to search for"
                    },
                    "repo": {
                        "type": "string",
                        "description": "Optional: filter by repository"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 50,
                        "description": "Maximum results"
                    }
                },
                "required": ["file_type"]
            }
        ),
        
        # ===== ANALYSIS TOOLS =====
        Tool(
            name="get_stats",
            description="Get statistics about the indexed knowledge base",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        
        Tool(
            name="analyze_dependencies",
            description="Analyze dependency graph for a specific file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to analyze"
                    }
                },
                "required": ["path"]
            }
        ),
    ]


@mcp_server.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls"""
    
    try:
        if name == "index_file":
            file_knowledge = FileKnowledge(
                path=arguments["path"],
                repo=arguments["repo"],
                file_type=FileType(arguments["file_type"]),
                technology=Technology(arguments["technology"]),
                summary=arguments["summary"],
                key_elements=arguments.get("key_elements", []),
                dependencies=arguments.get("dependencies", []),
                dependents=[],
                tags=arguments.get("tags", []),
                content_hash=arguments["content_hash"],
                file_metadata=arguments.get("file_metadata", {})
            )
            
            success = db.index_file(file_knowledge)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "success" if success else "error",
                    "message": f"{'Successfully indexed' if success else 'Failed to index'} {arguments['path']}",
                    "path": arguments["path"]
                }, indent=2)
            )]
        
        elif name == "index_batch":
            files = []
            for file_data in arguments["files"]:
                files.append(FileKnowledge(
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
            
            results = db.index_batch(files)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "results": results,
                    "message": f"Indexed {results['success']} files, {results['failed']} failed"
                }, indent=2)
            )]
        
        elif name == "search_knowledge":
            query = SearchQuery(
                query=arguments["query"],
                file_types=[FileType(ft) for ft in arguments.get("file_types", [])],
                technologies=[Technology(t) for t in arguments.get("technologies", [])],
                repos=arguments.get("repos"),
                tags=arguments.get("tags"),
                limit=arguments.get("limit", 10)
            )
            
            results = db.search_knowledge(query)
            
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
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "count": len(formatted),
                    "results": formatted
                }, indent=2)
            )]
        
        elif name == "get_file_context":
            result = db.get_file_context(arguments["path"])
            
            if result:
                return [TextContent(
                    type="text",
                    text=json.dumps({
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
                )]
            else:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "not_found",
                        "message": f"File not found: {arguments['path']}"
                    }, indent=2)
                )]
        
        elif name == "find_related":
            results = db.find_related(
                arguments["path"],
                arguments.get("limit", 10)
            )
            
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
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "count": len(formatted),
                    "related_files": formatted
                }, indent=2)
            )]
        
        elif name == "search_by_type":
            results = db.search_by_type(
                arguments["file_type"],
                arguments.get("repo"),
                arguments.get("limit", 50)
            )
            
            formatted = [
                {
                    "path": r.path,
                    "repo": r.repo,
                    "summary": r.summary,
                    "tags": r.tags
                }
                for r in results
            ]
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "file_type": arguments["file_type"],
                    "count": len(formatted),
                    "files": formatted
                }, indent=2)
            )]
        
        elif name == "get_stats":
            stats = db.get_stats()
            
            return [TextContent(
                type="text",
                text=json.dumps({
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
            )]
        
        elif name == "analyze_dependencies":
            deps = db.analyze_dependencies(arguments["path"])
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "dependency_graph": {
                        "root": deps.root,
                        "dependencies": deps.dependencies,
                        "dependents": deps.dependents,
                        "depth": deps.depth
                    }
                }, indent=2)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "error",
                    "message": f"Unknown tool: {name}"
                }, indent=2)
            )]
    
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "error",
                "message": str(e),
                "tool": name
            }, indent=2)
        )]


# ==================== SSE ENDPOINT ====================

@app.get("/sse")
async def handle_sse(request: Request):
    """SSE endpoint for MCP communication"""
    
    async def event_generator():
        """Generate SSE events for MCP protocol"""
        from mcp.server.sse import SseServerTransport
        
        # Create SSE transport
        async with SseServerTransport("/message") as transport:
            # Connect transport to MCP server
            async with transport.connect_sse(
                mcp_server,
                lambda: logger.info("MCP client connected")
            ) as streams:
                # Run the server
                await mcp_server.run(
                    streams[0],
                    streams[1],
                    mcp_server.create_initialization_options()
                )
    
    return EventSourceResponse(event_generator())


@app.post("/message")
async def handle_message(request: Request):
    """Handle MCP messages via POST"""
    data = await request.json()
    logger.info(f"Received message: {data}")
    return JSONResponse({"status": "ok"})


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
            "message": "/message",
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
