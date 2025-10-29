# 🧠 Emperion Knowledge Base - Remote MCP Server

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![MCP](https://img.shields.io/badge/MCP-1.1-orange.svg)](https://modelcontextprotocol.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**AI-powered code intelligence system** that bridges your local repositories with Claude Desktop through the Model Context Protocol (MCP). Store, search, and analyze structured knowledge about your codebase.

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
         │ SSE/Remote Connection
         ▼
┌─────────────────────────────────────────────┐
│     DigitalOcean App Platform ($5/mo)       │
│  ┌─────────────────────────────────────┐  │
│  │  Emperion Knowledge Base (FastAPI)   │  │
│  │  • Index files                        │  │
│  │  • Search knowledge                   │  │
│  │  • Analyze dependencies               │  │
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
- Claude Desktop installed
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

Follow the detailed [**SUPABASE_SETUP.md**](SUPABASE_SETUP.md) guide.

**Quick version:**

1. Create project at https://supabase.com/dashboard
2. Get connection string from: Settings → Database → Connection String → URI
3. Copy the PostgreSQL connection string:
   ```
   postgresql://postgres.xxx:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres
   ```

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

### 4. Connect Claude Desktop

Edit: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/path/to/your/repos"
      ]
    },
    "emperion-knowledge": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-remote",
        "https://your-app.ondigitalocean.app/sse"
      ]
    }
  }
}
```

Restart Claude Desktop (Cmd+Q and reopen).

---

## 📖 Usage Examples

### Indexing Files

```
Hey Claude, use the filesystem MCP to read /emperion/azure-iac/main.bicep 
and index it in the emperion-knowledge server.
```

Claude will:
1. Read the file locally
2. Extract key information (resources, dependencies, etc.)
3. Store in the remote knowledge base

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

---

## 🗂️ Project Structure

```
emperion-knowledge-base/
├── main.py                    # FastAPI app with SSE endpoint
├── database.py                # SQLAlchemy database layer
├── models.py                  # Pydantic models
├── config.py                  # Configuration management
├── requirements.txt           # Python dependencies
├── Procfile                   # DigitalOcean runtime config
├── app.yaml                   # App Platform specification
├── .env.example               # Environment template
├── SUPABASE_SETUP.md          # Supabase setup guide
├── SUPABASE_QUICK_GUIDE.md    # Quick visual guide
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
postgresql://postgres.[project-ref]:[password]@db.[project-ref].supabase.co:5432/postgres
```

Get from: Supabase Dashboard → Settings → Database → Connection String

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
| `/health` | GET | Health check |
| `/sse` | GET | SSE endpoint for MCP |
| `/message` | POST | MCP message handler |

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
```

### Test Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Get stats
curl http://localhost:8000/
```

---

## 🆘 Troubleshooting

### "Connection refused" or "timeout"

**Check:**
1. ✅ Is your Supabase project status "Active"?
2. ✅ Did you replace `[YOUR-PASSWORD]` in the connection string?
3. ✅ Is the connection string in the correct format?

**Test connection:**
```bash
psql "postgresql://postgres:password@db.xxx.supabase.co:5432/postgres"
```

### "Password authentication failed"

**Solution:**
1. Go to Supabase → Settings → Database
2. Click "Reset Database Password"
3. Update DATABASE_URL with new password

### "Health check failed" in DigitalOcean

**Check logs:**
```
Apps → Your App → Runtime Logs
```

Look for database connection errors.

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
- [Supabase](https://supabase.com/) - PostgreSQL database platform
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [DigitalOcean](https://www.digitalocean.com/) - Cloud infrastructure

---

## 📚 Documentation

- **[SUPABASE_SETUP.md](SUPABASE_SETUP.md)** - Complete Supabase setup guide
- **[SUPABASE_QUICK_GUIDE.md](SUPABASE_QUICK_GUIDE.md)** - Visual quick reference
- **[CHECKLIST.md](CHECKLIST.md)** - Pre-deployment checklist

---

## 📞 Support

- 🐛 Issues: [GitHub Issues](https://github.com/YOUR_USERNAME/emperion-knowledge-base/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/YOUR_USERNAME/emperion-knowledge-base/discussions)

---

**Built with ❤️ by Malcon Albuquerque for the Emperion Project**

**Powered by:** Supabase (PostgreSQL) + DigitalOcean (Hosting) + Anthropic MCP
