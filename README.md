# 🧠 Emperion Knowledge Base - Remote MCP Server

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![MCP](https://img.shields.io/badge/MCP-1.1-orange.svg)](https://modelcontextprotocol.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**AI-powered code intelligence system** that bridges your local repositories with Claude Desktop through the Model Context Protocol (MCP). Store, search, and analyze structured knowledge about your codebase to get better AI assistance.

---

## 🎯 What is this?

A **remote MCP server** that:

1. 🗄️ **Stores** structured knowledge about your code files
2. 🔍 **Searches** through summaries, dependencies, and tags
3. 🧠 **Analyzes** relationships between files and components
4. 🤝 **Integrates** seamlessly with Claude Desktop

### The Workflow

```
┌──────────────────┐         ┌─────────────────────┐
│  Claude Desktop  │ ◄─────► │  Filesystem MCP     │
│   (Local AI)     │         │  (Read local files) │
└────────┬─────────┘         └─────────────────────┘
         │
         │ SSE/Remote Connection
         ▼
┌─────────────────────────────────────────────┐
│     DigitalOcean App Platform               │
│                                             │
│  ┌─────────────────────────────────────┐  │
│  │  Emperion Knowledge Base (FastAPI)   │  │
│  │  • Index files                        │  │
│  │  • Search knowledge                   │  │
│  │  • Analyze dependencies               │  │
│  └──────────────┬──────────────────────┘  │
│                 │                           │
│  ┌──────────────▼──────────────────────┐  │
│  │  PostgreSQL 16 (Managed Database)    │  │
│  │  • File index with GIN indexes       │  │
│  │  • Full-text search                  │  │
│  │  • Metadata storage (JSONB)          │  │
│  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
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

# Edit .env with your database credentials
nano .env
```

### 2. Deploy to DigitalOcean

Follow the detailed [**DEPLOYMENT_GUIDE.md**](DEPLOYMENT_GUIDE.md) for step-by-step instructions.

**TL;DR:**
1. Create Managed PostgreSQL database
2. Push code to GitHub
3. Deploy via App Platform
4. Configure environment variables
5. Connect Claude Desktop

### 3. Test Locally (Optional)

```bash
# Install dependencies
pip install -r requirements.txt

# Set DATABASE_URL in .env
export $(cat .env | xargs)

# Run server
python main.py
```

Server runs on: `http://localhost:8000`

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
├── main.py                 # FastAPI app with SSE endpoint
├── database.py             # SQLAlchemy database layer
├── models.py               # Pydantic models
├── config.py               # Configuration management
├── requirements.txt        # Python dependencies
├── Procfile                # DigitalOcean runtime config
├── app.yaml                # App Platform specification
├── .env.example            # Environment template
├── DEPLOYMENT_GUIDE.md     # Detailed deployment steps
├── README.md               # This file
└── LICENSE                 # MIT License
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | ✅ Yes | - |
| `MCP_SECRET_KEY` | Secret key for security | ✅ Yes | - |
| `ALLOWED_ORIGINS` | CORS origins (comma-separated) | No | `*` |
| `LOG_LEVEL` | Logging level | No | `INFO` |
| `RATE_LIMIT_PER_HOUR` | API rate limit | No | `100` |
| `MAX_FILE_SIZE_MB` | Max file size to index | No | `10` |

### Claude Desktop Config

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

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
| `metadata` | JSON | Additional metadata |

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

## 💰 Cost Estimate

**Using DigitalOcean's $200 free credits:**

| Resource | Cost/Month | Free Months |
|----------|------------|-------------|
| PostgreSQL (Basic 1GB) | $15 | 13 months |
| App Platform (Basic) | $5 | 40 months |
| **Total** | **$20** | **10 months** |

After credits: $20/month or downgrade to free tier.

---

## 🧪 Development

### Run Tests

```bash
pytest tests/
```

### Local Development

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Add new feature"

# Apply migrations
alembic upgrade head
```

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
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [DigitalOcean](https://www.digitalocean.com/) - Cloud infrastructure

---

## 📞 Support

- 📧 Email: your.email@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/YOUR_USERNAME/emperion-knowledge-base/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/YOUR_USERNAME/emperion-knowledge-base/discussions)

---

**Built with ❤️ by Malcon Albuquerque for the Emperion Project**
