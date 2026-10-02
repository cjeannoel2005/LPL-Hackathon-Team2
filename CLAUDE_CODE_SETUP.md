# 🤖 Claude Code Setup for Team

**For LPL Hackathon Team 2 - AWS Cloud Shell**

This guide helps team members set up Claude Code in their Cloud Shell environment.

---

## Prerequisites

- Access to this GitHub repository: https://github.com/omgitzjoe/LPL-Hackathon-Team2
- AWS Cloud Shell access
- GitHub personal access token (for cloning private repos)

---

## Quick Setup (5 minutes)

### 1. Clone the Repository

```bash
cd ~
git clone https://github.com/omgitzjoe/LPL-Hackathon-Team2.git
cd LPL-Hackathon-Team2
```

**If private repo, use personal access token:**
```bash
git clone https://YOUR_TOKEN@github.com/omgitzjoe/LPL-Hackathon-Team2.git
```

### 2. Check Disk Space

```bash
df -h /home/cloudshell-user
```

You need at least **200MB free**. Cloud Shell typically provides ~1GB home directory.

**If low on space:**
```bash
# Clean npm cache
rm -rf ~/.npm ~/.cache

# Clean AWS CLI cache
rm -rf ~/.aws/cli/cache
```

### 3. Configure npm to Use ~/.npm-global

```bash
mkdir -p ~/.npm-global
npm config set prefix '~/.npm-global'
```

### 4. Add npm-global to PATH

Add to `~/.bashrc` (only if not already there):
```bash
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

### 5. Install Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

**Expected output:**
```
added X packages in Ys
```

### 6. Verify Installation

```bash
claude --version
```

**Should show:** `2.1.xxx (Claude Code)`

### 7. Authenticate Claude Code

```bash
claude auth login
```

Follow the prompts to authenticate with your Anthropic account.

---

## Project-Specific Setup

### Load Project Context

The repository already contains `CLAUDE.md` which Claude Code will automatically read. This provides:
- Architecture overview
- Development commands
- Troubleshooting guides
- AWS service configuration

### Local Settings

A `.claude/settings.local.json` file exists for local-only settings (not committed to git). Current permissions allow:
- Running Claude commands
- npm configuration

---

## Common Issues & Solutions

### ❌ "command not found: claude"

**Solution:** PATH not configured correctly
```bash
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

### ❌ "EACCES: permission denied"

**Solution:** npm trying to write to system directory
```bash
npm config set prefix '~/.npm-global'
npm install -g @anthropic-ai/claude-code
```

### ❌ "No space left on device"

**Solution:** Cloud Shell home directory full
```bash
# Check usage
df -h /home/cloudshell-user

# Clean caches
rm -rf ~/.npm ~/.cache ~/.aws/cli/cache

# If still insufficient, work in /tmp (loses data on session end)
cd /tmp
git clone https://github.com/omgitzjoe/LPL-Hackathon-Team2.git
```

### ❌ "Failed to authenticate"

**Solution:** 
1. Visit https://claude.ai and sign up/login
2. Run `claude auth login` again
3. Follow browser authentication flow

---

## Team Collaboration Tips

### 1. Keep CLAUDE.md Updated
When you discover new patterns or solutions, update `CLAUDE.md` so Claude Code can help other team members automatically.

### 2. Use .env for AWS Configuration
Each team member should create their own `.env` file (gitignored):
```bash
cp .env.example .env
# Edit with your AWS OpenSearch endpoint
```

### 3. Share .claude/settings.json (Optional)
If the team wants shared permissions/settings, create `.claude/settings.json` (committed) for project-wide config. Use `.claude/settings.local.json` for personal overrides.

### 4. Git Workflow
```bash
# Always pull latest before starting work
git pull origin main

# Create feature branches
git checkout -b feature/your-feature-name

# Commit regularly
git add .
git commit -m "Description of changes"

# Push to share with team
git push origin feature/your-feature-name
```

### 5. Ask Claude Code for Help
```bash
# Start interactive session
claude

# Ask questions like:
# "How do I deploy the infrastructure?"
# "What's the RAG pipeline architecture?"
# "Help me debug this Bedrock error"
```

---

## Verify Complete Setup

Run this checklist:

```bash
# ✅ Claude Code installed
claude --version

# ✅ In project directory
pwd
# Should show: /home/cloudshell-user/LPL-Hackathon-Team2

# ✅ Project files present
ls -la
# Should see: rag_engine.py, app.py, infra/, CLAUDE.md

# ✅ Python dependencies installed
pip list | grep -E "(boto3|opensearch|streamlit|pypdf2)"

# ✅ AWS credentials configured
aws sts get-caller-identity
```

---

## Next Steps

After Claude Code is set up:

1. **Configure AWS** - Follow [AWS_SETUP.md](AWS_SETUP.md)
2. **Deploy Infrastructure** - Follow [QUICKSTART.md](QUICKSTART.md)
3. **Start Coding** - Ask Claude Code to help with development tasks

---

## Getting Help

**During Hackathon:**
- Ask team members in Slack/Teams
- Use Claude Code: `claude` then ask "How do I...?"
- Check project docs: `CLAUDE.md`, `README.md`, `AWS_SETUP.md`

**Claude Code Issues:**
- Claude Code documentation: https://github.com/anthropics/claude-code
- Check GitHub Issues: https://github.com/anthropics/claude-code/issues

**AWS/Project Issues:**
- Check `CLAUDE.md` for troubleshooting
- Review CloudFormation stack events in AWS Console
- Check CloudWatch logs for errors

---

## Cloud Shell Session Management

**Important:** Cloud Shell sessions timeout after ~20 minutes of inactivity.

**To preserve work:**
```bash
# Commit changes regularly
git add .
git commit -m "WIP: description"
git push

# Settings and Claude Code installation persist in home directory
# But /tmp directory is cleared on timeout!
```

**When session resumes:**
```bash
cd ~/LPL-Hackathon-Team2
git pull  # Get latest changes
# Continue working - Claude Code and npm-global persist
```

---

## Success! 🎉

You're now set up to use Claude Code with the LPL AI Assistant project.

**Test it out:**
```bash
claude
```

Then ask: "Explain the RAG architecture in this project"

Claude will read `CLAUDE.md` and provide context-aware help!
