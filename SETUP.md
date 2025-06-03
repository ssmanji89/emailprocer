# 🚀 EmailBot Development Setup Guide

## Overview
EmailBot is an enterprise-grade AI-powered email classification and escalation management system. This guide will help you set up a local development environment.

## Prerequisites

### Required Software
- **Python 3.11+** - Main application runtime
- **Node.js 18+** - Frontend development
- **PostgreSQL 15+** - Primary database
- **Redis 7+** - Caching and session storage
- **Docker & Docker Compose** - Containerized deployment (optional)

### Required API Access
- **Microsoft 365 Tenant** - For email integration
- **OpenAI API Account** - For AI classification
- **Administrative Access** - To configure email permissions

## 🔧 Environment Configuration

### Step 1: Copy Environment Templates
```bash
# Copy the environment template files
cp env.example .env
cp test.env.example test.env
```

### Step 2: Configure Your Credentials

#### 2.1 Microsoft 365 Setup
1. **Register Application in Azure Portal**:
   - Go to [Azure Portal](https://portal.azure.com)
   - Navigate to "Azure Active Directory" > "App registrations"
   - Click "New registration"
   - Set redirect URI to `http://localhost:8000/auth/callback`

2. **Configure Application Permissions**:
   - Add Microsoft Graph permissions:
     - `Mail.Read` (Application)
     - `Mail.ReadWrite` (Application)
     - `User.Read.All` (Application)
   - Grant admin consent for your organization

3. **Update Environment Variables**:
   ```bash
   # In your .env file:
   EMAILBOT_M365_TENANT_ID=your-actual-tenant-id
   EMAILBOT_M365_CLIENT_ID=your-actual-client-id
   EMAILBOT_M365_CLIENT_SECRET=your-actual-client-secret
   EMAILBOT_TARGET_MAILBOX=your-test-email@your-domain.com
   ```

#### 2.2 OpenAI API Setup
1. **Get API Key**:
   - Visit [OpenAI API Platform](https://platform.openai.com/api-keys)
   - Create a new API key
   - Set usage limits and billing alerts

2. **Update Environment Variable**:
   ```bash
   # In your .env file:
   OPENAI_API_KEY=sk-proj-your-actual-openai-key
   ```

#### 2.3 Database Configuration
1. **PostgreSQL Setup**:
   ```bash
   # Create database and user
   sudo -u postgres psql
   CREATE DATABASE emailbot;
   CREATE USER emailbot WITH PASSWORD 'your_secure_password';
   GRANT ALL PRIVILEGES ON DATABASE emailbot TO emailbot;
   \q
   ```

2. **Update Environment Variable**:
   ```bash
   # In your .env file:
   DATABASE_URL=postgresql+asyncpg://emailbot:your_secure_password@localhost:5432/emailbot
   ```

#### 2.4 Redis Configuration
1. **Redis Setup**:
   ```bash
   # Ubuntu/Debian
   sudo apt install redis-server
   
   # macOS
   brew install redis
   
   # Start Redis
   redis-server
   ```

2. **Update Environment Variable**:
   ```bash
   # In your .env file (set password if Redis requires auth):
   REDIS_URL=redis://localhost:6379/0
   REDIS_PASSWORD=your_redis_password  # Optional
   ```

#### 2.5 Security Configuration
Generate secure keys for encryption:
```bash
# Generate 32-character encryption key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update in your .env file:
ENCRYPTION_KEY=your-generated-32-character-key
JWT_SECRET_KEY=your-generated-jwt-secret
SESSION_SECRET=your-generated-session-secret
MASTER_ENCRYPTION_KEY=your-generated-master-key
```

#### 2.6 Team Configuration
Update team member email addresses:
```bash
# In your .env file:
DEFAULT_IT_ADMIN_EMAIL=your-it-admin@your-domain.com
DEFAULT_HELPDESK_EMAIL=your-helpdesk@your-domain.com
DEFAULT_SYSTEM_ADMIN_EMAIL=your-sysadmin@your-domain.com
# ... continue for other team roles
```

## 🛠️ Installation and Setup

### Option A: Docker Setup (Recommended)
```bash
# Start all services with Docker
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f emailbot
```

### Option B: Manual Setup
```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Run database migrations
python scripts/migrate.py

# 3. Start Redis
redis-server

# 4. Start the application
python -m app.main
```

### Option C: Development Setup
```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install development dependencies
pip install -r requirements-dev.txt

# 4. Set up pre-commit hooks
pre-commit install

# 5. Run in development mode
python -m app.main --reload
```

## 🎯 Verification

### Test Your Setup
```bash
# 1. Health check
curl http://localhost:8000/health

# 2. Test email processing (replace with your test email)
curl -X POST http://localhost:8000/process/trigger \
  -H "Content-Type: application/json" \
  -d '{"mailbox": "test@your-domain.com"}'

# 3. Check API documentation
# Visit: http://localhost:8000/docs
```

### Common Issues and Solutions

#### Issue: "Authentication failed"
- **Solution**: Verify your M365 credentials and permissions
- Check tenant ID, client ID, and client secret
- Ensure admin consent is granted

#### Issue: "OpenAI API error"
- **Solution**: Verify your OpenAI API key and billing
- Check API key format and validity
- Ensure sufficient credits in your account

#### Issue: "Database connection failed"
- **Solution**: Verify PostgreSQL is running and credentials are correct
- Check database URL format
- Ensure database and user exist

#### Issue: "Redis connection failed"
- **Solution**: Ensure Redis is running
- Check Redis URL and password (if configured)
- Verify Redis is accessible on the specified port

## 🔒 Security Best Practices

### Environment Files
- **NEVER** commit `.env` files with real credentials
- Use different credentials for development, testing, and production
- Rotate API keys regularly
- Use strong, unique passwords for all services

### Development Guidelines
- Use test email accounts for development
- Keep production and development environments separate
- Use environment variables for all sensitive configuration
- Enable debug logging only in development

### Team Collaboration
- Share setup instructions, not credentials
- Use a secure password manager for team credentials
- Document any special configuration requirements
- Keep environment templates updated

## 📚 Next Steps

### Development Workflow
1. **Read the Documentation**: Check `/docs` folder for detailed guides
2. **Explore the API**: Visit http://localhost:8000/docs for interactive API documentation
3. **Run Tests**: Execute `python -m pytest` to run the test suite
4. **Check Code Quality**: Run `flake8` and `black` for code formatting

### Key Development Areas
- **Frontend Dashboard**: Located in `/dashboard` (Next.js application)
- **API Endpoints**: Located in `/app/api` (FastAPI routes)
- **Core Services**: Located in `/app/services` (Business logic)
- **Configuration**: Located in `/app/config` (Settings and configuration)

### Monitoring and Debugging
- **Application Logs**: Check `logs/emailbot.log`
- **Metrics**: Visit http://localhost:9090 (Prometheus)
- **Performance**: Use the built-in monitoring dashboard

## 🆘 Getting Help

### Resources
- **API Documentation**: http://localhost:8000/docs
- **Project README**: See main README.md for architecture overview
- **Code Examples**: Check `/tests` directory for usage examples

### Troubleshooting
- Check application logs for error details
- Verify all environment variables are set correctly
- Ensure all required services are running
- Test API endpoints individually to isolate issues

### Support
- Review error messages carefully
- Check the troubleshooting section above
- Ensure all prerequisites are properly installed
- Verify network connectivity for external API calls

---

**Note**: This setup guide uses placeholder values. Replace all `your-*` values with your actual configuration. Never commit real credentials to version control. 