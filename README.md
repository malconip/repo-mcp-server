# 🧠 Emperion Knowledge Base - Remote MCP Server

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.10+-green.svg)](https://github.com/jlowin/fastmcp)
[![MCP](https://img.shields.io/badge/MCP-1.9-orange.svg)](https://modelcontextprotocol.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**AI-powered code intelligence system** that bridges your local repositories with Claude Desktop through the Model Context Protocol (MCP). Store, search, and analyze structured knowledge about your codebase.

> 🚀 **NEW!** Now using **Streamable HTTP** transport (the official recommended protocol) with **FastMCP** for simplified deployment!

---

## 🎯 What is this?

A **remote MCP server** that:

1. 🗄️ **Stores** structured knowledge about your code files
2. 🔍 **Searches** through summaries, dependencies, and tags
3. 🧠 **Analyzes** relationships between files and components
4. 🤝 **Integrates** seamlessly with Claude Desktop

### The Architecture

```
┌──────────────────┐         ┌─────────────────────┐
│  Claude Desktop  │ ◄─────► │  Filesystem MCP     │
│   (Local AI)     │         │  (Read local files) │
└────────┬─────────┘         └─────────────────────┘
         │
         │ Streamable HTTP (Single Endpoint!)
         ▼
┌─────────────────────────────────────────────┐
│     DigitalOcean App Platform ($5/mo)       │
│  ┌─────────────────────────────────────┐  │
│  │  Emperion Knowledge Base (FastMCP)   │  │
│  │  • Streamable HTTP on /mcp           │  │
│  │  • Stateless deployment              │  │
│  │  • 8 powerful tools                  │  │
│  └──────────────┬──────────────────────┘  │
└─────────────────┼────────────────────────────┘
                  │
┌─────────────────▼────────────────────────┐
│     Supabase PostgreSQL (FREE!)          │
│  • 500 MB database storage               │
│  • SSL/TLS encryption                    │
│  • Automatic backups                     │
│  • Connection pooling                    │
└──────────────────────────────────────────┘
```

**Why Streamable HTTP?**
- ✅ **Single endpoint** (`/mcp`) instead of multiple endpoints
- ✅ **Stateless** - perfect for cloud platforms
- ✅ **Official standard** - SSE is being deprecated
- ✅ **Simpler** - less configuration, easier debugging

---

## ✨ Features

### 🔧 **8 Powerful Tools**

| Tool | Description |
|------|-------------|
| `index_file` | Index a single file's knowledge |
| `index_batch` | Index multiple files efficiently |
| `search_knowledge` | Semantic search through code |
| `get_file_context` | Get complete file information |
| `find_related` | Find related files |
| `search_by_type` | Filter by file type (Bicep, C#, Python, etc.) |
| `get_stats` | Knowledge base statistics |
| `analyze_dependencies` | Dependency graph analysis |

### 📂 **Supported File Types**

- **Infrastructure**: Bicep, Terraform, Helm, YAML
- **Backend**: C#, Python, JavaScript, TypeScript
- **DevOps**: PowerShell, Bash, Dockerfile
- **Config**: JSON, ENV files
- **Docs**: Markdown

### 🏷️ **Technology Categories**

- Infrastructure as Code
- Backend Development
- Frontend Development
- DevOps Automation
- Testing
- Documentation
- Configuration

---

## 🚀 Quick Start

### Prerequisites

- **Supabase account** ([Free PostgreSQL](https://supabase.com)) - **Required**
- DigitalOcean account ([Get $200 free credits](https://try.digitalocean.com/))
- GitHub account
- Claude Desktop installed (with MCP support)
- Python 3.11+

### 1. Clone & Setup

```bash
git clone https://github.com/YOUR_USERNAME/emperion-knowledge-base.git
cd emperion-knowledge-base

# Copy environment template
cp .env.example .env

# Edit .env with your Supabase credentials
nano .env
```

### 2. Setup Supabase Database (2 minutes)

1. Create project at https://supabase.com/dashboard
2. Get connection string from: **Settings → Database → Connection String → URI**
3. Copy the PostgreSQL connection string (Transaction mode with pooler):
   ```
   postgresql://postgres.xxx:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```
4. Update `DATABASE_URL` in your `.env` file

### 3. Deploy to DigitalOcean

1. Push code to GitHub
2. Go to https://cloud.digitalocean.com/apps
3. Create App → Select your GitHub repo
4. Add **encrypted** environment variables:
   - `DATABASE_URL` - Your Supabase connection string
   - `MCP_SECRET_KEY` - Generate with: `openssl rand -hex 32`
   - `LOG_LEVEL` - `INFO`
   - `ALLOWED_ORIGINS` - `https://claude.ai`
5. Deploy!

Your app will be available at: `https://your-app.ondigitalocean.app`

### 4. Connect Claude Desktop

**For Users WITH Claude Pro/Max/Team/Enterprise:**

Go to Claude Desktop → Settings → Connectors → Add Custom Connector

Enter your MCP endpoint URL:
```
https://your-app.ondigitalocean.app/mcp
```

**For Users WITHOUT Pro Plans (using local proxy):**

Edit: `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/path/to/your/emperion/repos"
      ]
    },
    "emperion-knowledge": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://your-app.ondigitalocean.app/mcp"
      ]
    }
  }
}
```

**Restart Claude Desktop** completely (Cmd+Q / File → Quit and reopen).

Look for the 🔨 hammer icon to confirm your server is connected!

---

## 📖 Usage Examples

### Indexing Files

```
Hey Claude, use the filesystem MCP to read /emperion/azure-iac/main.bicep 
and index it in the emperion-knowledge server.
```

Claude will:
1. Read the file locally with filesystem MCP
2. Extract key information (resources, dependencies, etc.)
3. Store in the remote knowledge base using Streamable HTTP

### Searching Knowledge

```
Search the emperion-knowledge for "Azure storage configuration"
```

Returns:
- Relevant files
- Summaries
- Key elements
- Dependencies

### Analyzing Dependencies

```
Analyze dependencies for /emperion/IntakeAPI/Services/AuthService.cs
```

Returns:
- Direct dependencies
- Dependents (what depends on this file)
- Dependency depth

### Getting Statistics

```
Get stats from emperion-knowledge
```

Returns:
- Total files indexed
- Files by type (Bicep, C#, Python, etc.)
- Files by repository
- Files by technology
- Last indexed timestamp

---

## 🗂️ Project Structure

```
emperion-knowledge-base/
├── main.py                    # FastMCP server with Streamable HTTP
├── database.py                # SQLAlchemy database layer
├── models.py                  # Pydantic models
├── config.py                  # Configuration management
├── requirements.txt           # Python dependencies (with FastMCP)
├── Procfile                   # DigitalOcean runtime config
├── app.yaml                   # App Platform specification
├── .env.example               # Environment template
├── README.md                  # This file
└── LICENSE                    # MIT License
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | Supabase PostgreSQL connection string | ✅ Yes |
| `MCP_SECRET_KEY` | Secret key for security | ✅ Yes |
| `ALLOWED_ORIGINS` | CORS origins (comma-separated) | No (default: `https://claude.ai`) |
| `LOG_LEVEL` | Logging level | No (default: `INFO`) |
| `RATE_LIMIT_PER_HOUR` | API rate limit | No (default: `100`) |
| `MAX_FILE_SIZE_MB` | Max file size to index | No (default: `10`) |

### Supabase Connection String Format

```
postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
```

Get from: **Supabase Dashboard → Settings → Database → Connection String → URI (Transaction mode)**

---

## 📊 Database Schema

### `file_index` Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Primary key |
| `path` | String(500) | Full file path (unique) |
| `repo` | String(100) | Repository name |
| `file_type` | String(50) | File type enum |
| `technology` | String(50) | Technology category |
| `summary` | Text | File purpose summary |
| `key_elements` | JSON | Important elements (array) |
| `dependencies` | JSON | File dependencies (array) |
| `dependents` | JSON | Dependent files (array) |
| `tags` | JSON | Searchable tags (array) |
| `content_hash` | String(64) | Content hash for change detection |
| `indexed_at` | DateTime | Index timestamp |
| `file_metadata` | JSON | Additional metadata |

**Indexes:**
- `idx_repo_filetype` (repo, file_type)
- `idx_technology` (technology)
- `idx_indexed_at` (indexed_at)
- Unique constraint on `path`

---

## 🛣️ API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Server info |
| `/health` | GET | Health check with stats |
| `/mcp` | POST | **MCP Streamable HTTP endpoint** |
| `/docs` | GET | FastAPI auto-generated docs |

---

## 💰 Cost Breakdown

### Total: $5/month

| Resource | Cost/Month | What You Get |
|----------|------------|--------------|
| **Supabase PostgreSQL** | **$0** | 500 MB storage, SSL, backups, pooling |
| **DigitalOcean App Platform** | **$5** | Python app hosting, SSL certificate |
| **TOTAL** | **$5** | Complete AI code intelligence! 🎉 |

### Free Tier Limits (Supabase)

- 500 MB database storage
- Unlimited API requests
- 2 GB bandwidth
- 50 MB file storage
- 7 days backup retention

**Enough for ~50,000 indexed files!**

---

## 🧪 Development

### Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="your-supabase-connection-string"
export MCP_SECRET_KEY="your-secret-key"

# Run server
python main.py

# Server runs on: http://localhost:8000
# MCP endpoint: http://localhost:8000/mcp
# Health check: http://localhost:8000/health
```

### Test Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Server info
curl http://localhost:8000/

# API docs (Swagger UI)
open http://localhost:8000/docs
```

### Test MCP Locally

```bash
# Install MCP inspector
pip install mcp-inspector

# Test your server
mcp-inspector http://localhost:8000/mcp
```

---

## 🆘 Troubleshooting

### "Connection refused" or "timeout"

**Check:**
1. ✅ Is your Supabase project status "Active"?
2. ✅ Did you replace `[YOUR-PASSWORD]` in the connection string?
3. ✅ Is the connection string in the correct format?
4. ✅ Are you using the **pooler** connection (port 6543)?

**Test connection:**
```bash
psql "postgresql://postgres:password@aws-0-region.pooler.supabase.com:6543/postgres"
```

### "Password authentication failed"

**Solution:**
1. Go to Supabase → Settings → Database
2. Click "Reset Database Password"
3. Update DATABASE_URL with new password
4. Redeploy your DigitalOcean app

### "Health check failed" in DigitalOcean

**Check logs:**
```
Apps → Your App → Runtime Logs
```

Look for database connection errors or missing environment variables.

### Claude Desktop not showing tools

**Check:**
1. ✅ Completely restart Claude Desktop (Quit and reopen)
2. ✅ Look for 🔨 hammer icon in Claude
3. ✅ Check Claude Desktop logs: `~/Library/Logs/Claude/` (Mac)
4. ✅ Verify your MCP endpoint is accessible: `curl https://your-app.ondigitalocean.app/health`

---

## 🔄 Migration from SSE to Streamable HTTP

If you had the old SSE version, here's what changed:

**OLD (SSE):**
```python
# Multiple endpoints
@app.get("/sse")  # SSE connection
Mount("/messages/", sse_transport.handle_post_message)  # Message handler
```

**NEW (Streamable HTTP):**
```python
# Single endpoint
app.mount("/mcp", mcp.streamable_http_app())  # Everything handled here!
```

**Benefits:**
- ✅ 1 endpoint instead of 2
- ✅ Stateless (better for cloud)
- ✅ Simpler configuration
- ✅ Official standard

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Anthropic MCP](https://modelcontextprotocol.io/) - Model Context Protocol
- [FastMCP](https://github.com/jlowin/fastmcp) - High-level MCP framework
- [Supabase](https://supabase.com/) - PostgreSQL database platform
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [DigitalOcean](https://www.digitalocean.com/) - Cloud infrastructure

---

## 📚 Additional Resources

- **[MCP Documentation](https://modelcontextprotocol.io/docs)** - Official MCP docs
- **[FastMCP Docs](https://gofastmcp.com/)** - FastMCP documentation
- **[Streamable HTTP Spec](https://spec.modelcontextprotocol.io/specification/basic/transports/#http-with-sse)** - Transport specification

---

## 📞 Support

- 🐛 Issues: [GitHub Issues](https://github.com/YOUR_USERNAME/emperion-knowledge-base/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/YOUR_USERNAME/emperion-knowledge-base/discussions)

---

**Built with ❤️ by Malcon Albuquerque for the Emperion Project**

**Powered by:** FastMCP + Supabase (PostgreSQL) + DigitalOcean (Hosting) + Anthropic MCP

🚀 **Now with Streamable HTTP - The future of MCP!**
