# 🚀 Deployment Guide - DigitalOcean App Platform

## 📋 Prerequisites

- DigitalOcean account (get $200 free credits: https://try.digitalocean.com/)
- GitHub account
- Claude Desktop installed locally

---

## 🎯 Step 1: Push Code to GitHub

```bash
cd /Users/malconalbuquerque/emperion/lab/repo-mcp-server

# Initialize git if not done
git init
git add .
git commit -m "Initial commit: Emperion Knowledge Base MCP Server"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/emperion-knowledge-base.git
git push -u origin main
```

---

## 🗄️ Step 2: Create Managed PostgreSQL Database

1. Go to DigitalOcean Dashboard → **Databases**
2. Click **Create Database**
3. Choose:
   - **Engine**: PostgreSQL 16
   - **Plan**: Basic (1 vCPU, 1 GB RAM) - **$15/month** (uses free credits!)
   - **Data center**: New York (NYC3) or nearest
   - **Name**: `emperion-kb-db`
4. Click **Create Database Cluster**
5. **Wait ~5 minutes** for provisioning

### 🔐 Get Connection String

After database is ready:

1. Click on your database → **Connection Details**
2. Copy the **Connection String** (starts with `postgresql://doadmin:...`)
3. **IMPORTANT**: Should look like:
   ```
   postgresql://doadmin:PASSWORD@your-db-do-user-123456-0.db.ondigitalocean.com:25060/defaultdb?sslmode=require
   ```

---

## ☁️ Step 3: Deploy to App Platform

### Option A: Using Web UI (Recommended)

1. Go to **Apps** → **Create App**
2. Choose **GitHub** as source
3. Select your repository: `emperion-knowledge-base`
4. Branch: `main`
5. Autodeploy: ✅ **Enabled**

#### Configure App Settings:

**Detected automatically:**
- ✅ Python runtime
- ✅ Procfile detected
- ✅ Port 8000

**Environment Variables** (add in UI):

```bash
DATABASE_URL = <paste your PostgreSQL connection string>  # Mark as SECRET ✅
MCP_SECRET_KEY = <generate with: openssl rand -hex 32>    # Mark as SECRET ✅
LOG_LEVEL = INFO
ALLOWED_ORIGINS = https://claude.ai
```

**Health Check:**
- Path: `/health`
- Port: 8000

6. Click **Next** → **Review** → **Create Resources**
7. **Wait ~3-5 minutes** for deployment

---

### Option B: Using CLI (Advanced)

```bash
# Install doctl
brew install doctl

# Authenticate
doctl auth init

# Create app from spec
doctl apps create --spec app.yaml

# Update environment secrets
doctl apps update YOUR_APP_ID --env DATABASE_URL=postgresql://...
doctl apps update YOUR_APP_ID --env MCP_SECRET_KEY=abc123...
```

---

## ✅ Step 4: Verify Deployment

After deployment completes:

1. **Get your app URL**: `https://your-app-name.ondigitalocean.app`

2. **Test endpoints**:

```bash
# Health check
curl https://your-app-name.ondigitalocean.app/health

# Root endpoint
curl https://your-app-name.ondigitalocean.app/

# Expected response:
{
  "name": "Emperion Knowledge Base MCP Server",
  "version": "1.0.0",
  "status": "running"
}
```

---

## 🖥️ Step 5: Connect Claude Desktop

Edit your Claude Desktop config:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/malconalbuquerque/emperion"
      ]
    },
    "emperion-knowledge": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-remote",
        "https://your-app-name.ondigitalocean.app/sse"
      ]
    }
  }
}
```

**IMPORTANT**: Replace `your-app-name` with your actual app name!

---

## 🧪 Step 6: Test in Claude Desktop

1. **Restart Claude Desktop completely** (Cmd+Q and reopen)

2. Start a new conversation and try:

```
Can you check the available tools from the emperion-knowledge server?
```

Expected tools:
- `index_file`
- `index_batch`
- `search_knowledge`
- `get_file_context`
- `find_related`
- `search_by_type`
- `get_stats`
- `analyze_dependencies`

---

## 📊 Step 7: Start Indexing!

Now you can ask Claude to index your repositories:

```
Using the filesystem MCP, read files from /emperion/azure-iac 
and index them in the emperion-knowledge server. Start with 
.bicep files first.
```

Claude will:
1. 🔍 Read files using **filesystem MCP** (local)
2. 🧠 Extract key information
3. 📝 Store in **emperion-knowledge MCP** (remote)

---

## 🔧 Troubleshooting

### Database Connection Issues

```bash
# Test database connection manually
psql "postgresql://doadmin:PASSWORD@your-db.db.ondigitalocean.com:25060/defaultdb?sslmode=require"
```

### App Logs

```bash
# View logs in DigitalOcean UI
Apps → Your App → Runtime Logs

# Or with CLI
doctl apps logs YOUR_APP_ID --type run
```

### Common Issues

**"Health check failed"**
- Check DATABASE_URL is correct
- Verify database is running
- Check logs for connection errors

**"Tools not showing in Claude"**
- Verify SSE endpoint: `https://your-app.ondigitalocean.app/sse`
- Check CORS settings in ALLOWED_ORIGINS
- Restart Claude Desktop completely

**"Permission denied"**
- Check MCP_SECRET_KEY is set
- Verify ALLOWED_ORIGINS includes `https://claude.ai`

---

## 💰 Cost Estimate

**Using Free Credits ($200):**
- PostgreSQL DB: $15/month
- App Platform: $5/month
- **Total**: $20/month → **10 months free!**

**After credits:**
- Can downgrade or delete if needed
- Or keep running at $20/month

---

## 🎉 Success!

You now have:
- ✅ Remote MCP server running 24/7
- ✅ Managed PostgreSQL database
- ✅ Claude Desktop connected
- ✅ Ready to index your Emperion repos!

---

## 📚 Next Steps

1. Index all your repositories
2. Try semantic search: "find Azure storage configs"
3. Analyze dependencies
4. Get project statistics

**Enjoy your AI-powered code intelligence system!** 🚀
