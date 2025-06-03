# Repository Setup Guide

This repository contains sanitized example files for public distribution. To set up a working development environment, follow these steps:

## 🔧 Local Development Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd emailprocer
```

### 2. Set Up Environment Files

**Copy example files and add real credentials:**

```bash
# Copy environment templates
cp env.example .env
cp test.env.example test.env

# Copy for local development
cp test.env test_local.env
```

### 3. Configure Real Credentials

Edit the following files with your actual credentials:

#### `.env` (Main configuration)
```bash
# Replace with your actual Microsoft 365 credentials
EMAILBOT_M365_TENANT_ID=your-real-tenant-id
EMAILBOT_M365_CLIENT_ID=your-real-client-id  
EMAILBOT_M365_CLIENT_SECRET=your-real-client-secret
EMAILBOT_TARGET_MAILBOX=your-real-email@your-domain.com

# Replace with your actual OpenAI API key
OPENAI_API_KEY=sk-proj-your-real-openai-key

# Set up your database and Redis
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/emailbot
REDIS_URL=redis://localhost:6379/0
```

#### `test.env` (Test configuration)
```bash
# Use test versions of your credentials
EMAILBOT_TARGET_MAILBOX=test@your-domain.com
OPENAI_API_KEY=sk-proj-your-test-openai-key
```

### 4. Update Company-Specific Settings

Replace example placeholders in your local configuration:

- `example.com` → `your-company.com`
- `admin@example.com` → `admin@your-company.com`
- `Your Company` → `Your Actual Company Name`

### 5. Verification

Run the health check to verify your setup:
```bash
python -m pytest tests/ -v
curl http://localhost:8000/health
```

## ⚠️ Security Notes

- **Never commit** real credentials to the repository
- Environment files with real data are in `.gitignore`
- Use separate API keys for development/testing/production
- Rotate credentials regularly

## 📁 File Structure

```
├── .env.example          # Template with placeholders
├── test.env.example      # Test template with placeholders  
├── .env                  # Your real config (git-ignored)
├── test.env              # Your test config (git-ignored)
└── test_local.env        # Your local test config (git-ignored)
```

## 🔄 Keeping Local Changes Private

Your local configuration files are automatically ignored by Git:
```bash
# These files stay local only:
.env
test.env  
test_local.env
*.env.backup
```

To verify what files will be committed:
```bash
git status --ignored
``` 