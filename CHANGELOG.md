# Changelog

All notable changes to the Emperion Knowledge Base MCP Server.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2025-10-29

### 🚀 **MAJOR REWRITE: FastMCP + Streamable HTTP**

Complete rewrite of the MCP server using the official recommended technologies.

### ✨ Added

- **FastMCP Framework**: High-level MCP framework for simplified development
- **Streamable HTTP Transport**: Single endpoint `/mcp` (official standard)
- **Stateless Deployment**: Perfect for cloud platforms like DigitalOcean
- **Enhanced Logging**: Better debugging with structured logs
- **Health Check**: Comprehensive health endpoint with database stats
- **Auto-Generated Docs**: FastAPI Swagger UI at `/docs`
- **Lifespan Management**: Proper startup/shutdown handling

### 🔄 Changed

- **Transport Protocol**: SSE → Streamable HTTP (official standard)
- **Framework**: Low-level MCP SDK → FastMCP
- **Endpoints**: Multiple endpoints → Single `/mcp` endpoint
- **Deployment**: Stateful → Stateless (cloud-native)
- **Configuration**: Simplified server setup
- **Dependencies**: Added `fastmcp>=2.10.0`

### 🗑️ Removed

- **SSE Transport**: Deprecated by Anthropic, removed in favor of Streamable HTTP
- **Multiple Endpoints**: `/sse` and `/messages/` consolidated into `/mcp`
- **Complex SSE Setup**: No longer needed with FastMCP
- **SseServerTransport**: Replaced by FastMCP's streamable HTTP

### 📖 Documentation

- Completely rewritten README.md with Streamable HTTP instructions
- New DEPLOYMENT_GUIDE.md with step-by-step cloud deployment
- Updated all examples for FastMCP usage
- Added troubleshooting section for common issues

### 🔧 Technical Details

**Before (v1.x - SSE):**
```python
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport

mcp_server = Server("emperion-knowledge-base")
sse_transport = SseServerTransport("/messages/")

@app.get("/sse")
async def handle_sse(request: Request):
    async with sse_transport.connect_sse(...) as streams:
        await mcp_server.run(streams[0], streams[1], ...)
```

**After (v2.0 - Streamable HTTP):**
```python
from fastmcp import FastMCP

mcp = FastMCP("emperion-knowledge-base", stateless_http=True)

@mcp.tool()
def index_file(...):
    # Tool implementation
    pass

app.mount("/mcp", mcp.streamable_http_app())
```

### 🎯 Benefits

1. **Simpler**: One endpoint instead of two
2. **Stateless**: Works better with cloud platforms
3. **Standard**: Official Anthropic recommendation
4. **Future-proof**: SSE being deprecated
5. **Better debugging**: Clearer error messages
6. **Easier testing**: Built-in MCP Inspector support

### ⚠️ Breaking Changes

- **Endpoint changed**: `/sse` → `/mcp`
- **Configuration**: Claude Desktop config must be updated
- **Dependencies**: `fastmcp` required
- **Python version**: Minimum 3.11 (FastMCP requirement)

### 📦 Migration Guide

For users upgrading from v1.x:

1. **Update Claude Desktop config:**
   ```json
   {
     "mcpServers": {
       "emperion-knowledge": {
         "command": "npx",
         "args": [
           "-y",
           "mcp-remote",
           "https://your-app.ondigitalocean.app/mcp"  // Changed from /sse
         ]
       }
     }
   }
   ```

2. **Update dependencies:**
   ```bash
   pip install -r requirements.txt  # Includes fastmcp
   ```

3. **Redeploy to DigitalOcean**:
   - Push new code to GitHub
   - DigitalOcean will auto-deploy

4. **Verify deployment:**
   ```bash
   curl https://your-app.ondigitalocean.app/health
   ```

---

## [1.0.0] - 2025-10-28

### Initial Release - SSE Transport

- Basic MCP server with SSE transport
- 8 core tools for code intelligence
- PostgreSQL database integration
- Supabase support
- DigitalOcean deployment configuration

### Features

- `index_file` - Index single files
- `index_batch` - Batch indexing
- `search_knowledge` - Keyword search
- `get_file_context` - File details
- `find_related` - Related files
- `search_by_type` - Filter by type
- `get_stats` - Statistics
- `analyze_dependencies` - Dependency analysis

---

## [Unreleased]

### Planned Features

- [ ] Semantic search with embeddings
- [ ] Vector database integration (Chroma/Pinecone)
- [ ] Advanced dependency graph visualization
- [ ] Real-time file watching
- [ ] Incremental updates
- [ ] Multi-language support
- [ ] Code complexity metrics
- [ ] Security vulnerability scanning
- [ ] API rate limiting
- [ ] Authentication/Authorization
- [ ] Webhook notifications
- [ ] Export/Import functionality

---

## Version History

- **v2.0.0** - Streamable HTTP with FastMCP (Current)
- **v1.0.0** - SSE transport (Deprecated)

---

## Support

For questions or issues:
- 🐛 [GitHub Issues](https://github.com/YOUR_USERNAME/emperion-knowledge-base/issues)
- 💬 [GitHub Discussions](https://github.com/YOUR_USERNAME/emperion-knowledge-base/discussions)
