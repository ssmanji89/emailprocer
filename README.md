# EmailBot - AI-Powered Email Classification System

**Current Status**: 🚀 **Phase 1 Complete** → Ready for Phase 2 (Security & Authentication)  
**Progress**: 12.5% Complete (1/8 phases implemented)

EmailBot is an intelligent email processing system for zgcompanies.com that automatically classifies and routes emails using OpenAI GPT-4, with confidence-based escalation to Microsoft Teams.

## 🎯 System Overview

### Target Configuration
- **Target Mailbox**: smanji@zgcompanies.com
- **M365 Tenant**: 20989ce2-8d98-49ee-b545-5e5462d827cd
- **AI Model**: OpenAI GPT-4 with custom classification prompts
- **Routing Logic**: Auto-handle (85%+), Suggest (60-84%), Escalate (<60%)

### Architecture
```
Email Inbox → Classification (GPT-4) → Confidence Routing → Teams Escalation
     ↓              ↓                      ↓                  ↓
   M365 API    OpenAI API         PostgreSQL/Redis      Teams API
```

## ✅ Phase 1: Core Infrastructure (COMPLETE)

### Implemented Components

#### 🐳 Docker Orchestration
- Multi-service container setup with PostgreSQL, Redis, monitoring
- Production-ready configuration with health checks
- Named volumes for data persistence

#### ⚙️ Configuration Management
- Comprehensive settings with Pydantic v2 validation
- Environment variable management with validation
- Support for development and production configurations

#### 🗄️ Database Framework
- Async SQLAlchemy setup with connection pooling
- Support for PostgreSQL (production) and SQLite (development)
- Health checks and retry mechanisms with exponential backoff

#### 🚀 Redis Caching
- Enhanced Redis client with JSON serialization
- Hash, list, and string operations
- Connection pooling and health monitoring
- Cache decorators for function results

#### 📊 Monitoring & Testing
- Prometheus monitoring configuration
- Infrastructure validation test suite
- Database initialization scripts

### Quick Start (Phase 1 Validation)

```bash
# 1. Setup environment
cp env.template .env
# Edit .env with actual credentials

# 2. Install dependencies
pip install -r requirements.txt
pip install email-validator  # Fix for Phase 1 issue

# 3. Test infrastructure
python test_phase1.py

# 4. Initialize database
python scripts/init_db.py

# 5. Start services (requires Docker)
docker-compose up -d
```

## 🔄 Phase 2: Security & Authentication (NEXT)

**Target Implementation**: Security layer required before external integrations

### Planned Components
1. **Security Framework** - Fernet encryption utilities and data protection
2. **Authentication Manager** - Enhanced Graph API authentication with security controls
3. **Encryption Utilities** - Field-level encryption for sensitive data
4. **Security Models** - Audit trails and security event tracking
5. **Security Middleware** - Request validation and rate limiting

### Prerequisites
- ✅ Phase 1 infrastructure completed
- ⚠️ Environment configuration (.env file creation needed)
- ⚠️ Dependency compatibility fixes required

## 🏗️ Development Roadmap

| Phase | Status | Components | Progress |
|-------|--------|------------|----------|
| **1. Core Infrastructure** | ✅ Complete | Docker, Database, Redis, Config | 100% |
| **2. Security & Auth** | 🔲 Ready | Encryption, Authentication, Audit | 0% |
| **3. M365 Integration** | 🔲 Pending | Graph API, Email Reading | 0% |
| **4. LLM Service** | 🔲 Pending | OpenAI GPT-4, Classification | 0% |
| **5. Email Processing** | 🔲 Pending | Workflow Engine, State Machine | 0% |
| **6. Teams Escalation** | 🔲 Pending | Team Assembly, Escalation Logic | 0% |
| **7. Monitoring** | 🔲 Pending | Health Checks, Metrics, Alerts | 0% |
| **8. Testing & Validation** | 🔲 Pending | End-to-end Testing, Validation | 0% |

## 📋 Environment Configuration

### Required Credentials
```bash
# Microsoft 365 (REQUIRED)
EMAILBOT_M365_TENANT_ID=20989ce2-8d98-49ee-b545-5e5462d827cd
EMAILBOT_M365_CLIENT_ID=d1f2693c-5d1a-49a4-bbfc-fb84b248a404
EMAILBOT_M365_CLIENT_SECRET=q~X8Q~Km6y5KpaZVHhsORjTvOtF5lRVs4.G1ZcX7
EMAILBOT_TARGET_MAILBOX=smanji@zgcompanies.com

# OpenAI (REQUIRED)  
OPENAI_API_KEY=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

# Security (REQUIRED - Generate new key for production)
ENCRYPTION_KEY=your_32_byte_base64_encryption_key

# Database (PostgreSQL for production, SQLite for development)
DATABASE_URL=postgresql+asyncpg://emailbot:password@localhost:5432/emailbot

# Redis
REDIS_URL=redis://localhost:6379/0
```

## 🔧 Technical Stack

### Infrastructure
- **Containerization**: Docker with multi-service orchestration
- **Database**: PostgreSQL 15 with async SQLAlchemy
- **Caching**: Redis 7 with persistence
- **Monitoring**: Prometheus with health checks

### Application
- **Framework**: FastAPI with async/await
- **Validation**: Pydantic v2 with comprehensive validation
- **Authentication**: Microsoft Graph API with MSAL
- **AI Processing**: OpenAI GPT-4 for email classification

### Security
- **Encryption**: Fernet symmetric encryption for sensitive data
- **Authentication**: Multi-factor with security controls
- **Audit**: Comprehensive logging and audit trails
- **Rate Limiting**: Request throttling and protection

## 📁 Project Structure

```
emailprocer/
├── app/
│   ├── config/              # ✅ Configuration management
│   │   ├── settings.py      # Comprehensive app settings
│   │   ├── database.py      # Async SQLAlchemy setup
│   │   └── redis_client.py  # Enhanced Redis client
│   ├── models/              # ✅ Data models (Phase 1)
│   │   └── email_models.py  # Email and processing models
│   ├── core/                # 🔲 Security & auth (Phase 2)
│   ├── integrations/        # 🔲 M365 & OpenAI (Phase 3-4)
│   ├── services/            # 🔲 Processing services (Phase 5)
│   ├── middleware/          # 🔲 Security middleware (Phase 2)
│   └── utils/               # 🔲 Utilities (Phase 2+)
├── docker/                  # ✅ Docker configuration
├── docs/                    # ✅ Comprehensive documentation
├── scripts/                 # ✅ Database and utility scripts
├── tests/                   # 🔲 Test suites (Phase 8)
├── monitoring/              # ✅ Prometheus configuration
├── docker-compose.yml       # ✅ Multi-service orchestration
├── Dockerfile              # ✅ Production container
├── requirements.txt        # ✅ Python dependencies
└── env.template            # ✅ Environment configuration
```

## 🚀 Getting Started for Developers

### For New Development Session
1. **Review Documentation**:
   - `docs/DEVELOPMENT_STATUS.md` - Current progress
   - `docs/SESSION_HANDOFF.md` - Continuation guide
   - `docs/SECURITY.md` - Phase 2 implementation patterns

2. **Setup Environment**:
   ```bash
   cp env.template .env  # Configure with actual credentials
   pip install -r requirements.txt
   pip install email-validator  # Fix Phase 1 compatibility
   ```

3. **Validate Infrastructure**:
   ```bash
   python test_phase1.py  # Should pass all tests
   ```

4. **Begin Phase 2**:
   - Follow RIPER-5 mode protocol
   - Implement security layer components
   - Reference `docs/SECURITY.md` for exact patterns

### For Production Deployment
1. **Setup Production Environment**:
   ```bash
   # Configure production .env with secure values
   # Generate secure encryption key
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

2. **Deploy Services**:
   ```bash
   docker-compose -f docker-compose.yml up -d
   ```

3. **Initialize Database**:
   ```bash
   docker exec emailbot-app python scripts/init_db.py
   ```

## 📖 Documentation

- **[Development Status](docs/DEVELOPMENT_STATUS.md)** - Current progress and next steps
- **[Session Handoff](docs/SESSION_HANDOFF.md)** - Development continuation guide  
- **[Implementation Guide](docs/IMPLEMENTATION.md)** - Code patterns and templates
- **[Security Requirements](docs/SECURITY.md)** - Security implementation patterns
- **[Integration Setup](docs/INTEGRATIONS.md)** - M365 and external service setup
- **[Operations Guide](docs/OPERATIONS.md)** - Monitoring and maintenance

## ⚠️ Known Issues & Fixes

### Environment Loading
- **Issue**: EMAILBOT_ prefixed variables may not load correctly
- **Fix**: Ensure `.env` file exists with proper variable names

### Dependencies  
- **Issue**: Missing email-validator causing model failures
- **Fix**: `pip install email-validator pydantic[email]`

### SQLAlchemy Compatibility
- **Issue**: async_sessionmaker import errors
- **Fix**: `pip install --upgrade sqlalchemy[asyncio]==2.0.23`

## 🎯 Final System Goals

EmailBot will automatically:
1. **Monitor** smanji@zgcompanies.com for new emails
2. **Classify** emails using OpenAI GPT-4 with specialized prompts
3. **Route** based on confidence levels (Auto/Suggest/Escalate)
4. **Escalate** complex issues to Microsoft Teams groups
5. **Audit** all processing with comprehensive logging

**Current Status**: Infrastructure foundation complete → Ready for security implementation → Then external integrations

---

**Contributing**: Follow RIPER-5 development protocol. See `docs/SESSION_HANDOFF.md` for development continuation. 