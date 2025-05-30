# EmailBot - M365 Email Processing Automation

An intelligent email processing bot for Microsoft 365 environments that automatically classifies, routes, and escalates IT department emails using LLM-powered analysis.

## 🚀 Features

- **LLM-Powered Classification**: Uses OpenAI GPT models to intelligently categorize emails
- **M365 Integration**: Native Microsoft Graph API integration for seamless email processing
- **Teams Escalation**: Automatic Teams group creation for complex issues requiring collaboration
- **Confidence-Based Routing**: Smart routing based on AI confidence scores
- **Pattern Discovery**: Identifies recurring email patterns for automation opportunities
- **Configurable CRM Integration**: Extensible architecture for external system integration
- **Docker Ready**: Fully containerized for easy deployment and scaling

## 📧 Email Categories

EmailBot automatically classifies emails into:

- **PURCHASING** - Purchase requests, vendor quotes, software licensing
- **SUPPORT** - Technical issues, system problems, user assistance
- **INFORMATION** - General inquiries, documentation requests
- **ESCALATION** - Urgent issues, executive requests, critical failures
- **CONSULTATION** - Strategic planning, architecture decisions

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   M365 Mailbox  │    │   EmailBot API  │    │  OpenAI GPT-4   │
│                 │◄──►│                 │◄──►│                 │
│  Graph API      │    │  FastAPI        │    │  Classification │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │ Teams Escalation│
                       │                 │
                       │ Auto-created    │
                       │ Groups          │
                       └─────────────────┘
```

## 🛠️ Prerequisites

- Python 3.11+
- Microsoft 365 tenant with admin access
- OpenAI API key
- Docker (optional, for containerized deployment)

## ⚙️ Installation & Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd emailprocer
```

### 2. Environment Configuration

Copy the environment template and configure your settings:

```bash
cp env.template .env
```

Edit `.env` with your actual values:

```bash
# Required M365 Configuration
EMAILBOT_M365_TENANT_ID=your-tenant-id-here
EMAILBOT_M365_CLIENT_ID=your-client-id-here
EMAILBOT_M365_CLIENT_SECRET=your-client-secret-here

# Target Mailbox
EMAILBOT_TARGET_MAILBOX=it-support@zgcompanies.com

# OpenAI Configuration
EMAILBOT_OPENAI_API_KEY=your-openai-api-key-here
EMAILBOT_OPENAI_MODEL=gpt-4
```

### 3. M365 App Registration

Register an application in your M365 tenant:

1. Go to Azure Portal → App Registrations
2. Create new registration
3. Add required API permissions:
   - `Mail.Read`
   - `Mail.Send`
   - `Chat.Create`
   - `ChatMember.ReadWrite`
   - `User.Read.All`
4. Grant admin consent
5. Create client secret

### 4. Python Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 5. Start the Application

```bash
# Development mode
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## 🔧 Configuration Options

### Confidence Thresholds

Configure how EmailBot handles different confidence levels:

```bash
EMAILBOT_CONFIDENCE_THRESHOLD_AUTO=85      # Auto-handle above this score
EMAILBOT_CONFIDENCE_THRESHOLD_SUGGEST=60  # Suggest responses above this
EMAILBOT_CONFIDENCE_THRESHOLD_REVIEW=40   # Require human review below this
```

### Processing Settings

```bash
EMAILBOT_POLLING_INTERVAL_MINUTES=5  # How often to check for new emails
EMAILBOT_BATCH_SIZE=10               # Number of emails to process per batch
EMAILBOT_MAX_RETRIES=3               # API retry attempts
```

### Teams Integration

```bash
EMAILBOT_TEAMS_DEFAULT_MEMBERS=["admin@zgcompanies.com"]
EMAILBOT_ESCALATION_FOLLOW_UP_HOURS=4
```

## 📊 API Endpoints

### Health & Status

- `GET /` - Basic application information
- `GET /health` - Component health check
- `GET /health/detailed` - Detailed system status
- `GET /config/validation` - Validate configuration

### Processing

- `POST /process/trigger` - Manually trigger email processing
- `GET /process/status` - Get processing status and statistics

### Example Health Check

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "components": {
    "m365_graph": "healthy",
    "email_client": "healthy",
    "llm_service": "healthy"
  }
}
```

## 🐳 Docker Deployment

### Build and Run

```bash
# Build image
docker build -t emailbot .

# Run container
docker run -d \
  --name emailbot \
  --env-file .env \
  -p 8000:8000 \
  emailbot
```

### Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f emailbot
```

## 🔍 Monitoring & Troubleshooting

### Logs

EmailBot provides structured logging. Configure log level:

```bash
EMAILBOT_LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
EMAILBOT_LOG_FORMAT=json # json or text
```

### Common Issues

1. **M365 Authentication Failures**
   - Verify tenant ID, client ID, and secret
   - Check API permissions and admin consent
   - Ensure target mailbox exists

2. **OpenAI API Errors**
   - Verify API key validity
   - Check rate limits and quotas
   - Monitor token usage

3. **Email Processing Issues**
   - Check mailbox permissions
   - Verify email filters and batch size
   - Review confidence thresholds

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_email_processor.py
```

## 🔮 Roadmap

- [ ] **Enhanced Pattern Discovery** - Machine learning for automatic rule generation
- [ ] **Multi-language Support** - Process emails in different languages
- [ ] **Advanced Analytics** - Dashboard for processing metrics and insights
- [ ] **Webhook Integration** - Real-time processing via Graph API webhooks
- [ ] **Custom Escalation Rules** - User-defined escalation workflows
- [ ] **Knowledge Base Integration** - Automatic responses from knowledge articles

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:

- Create an issue in this repository
- Check the troubleshooting section above
- Review the API documentation at `/docs` when running

## 🔧 Development

### Project Structure

```
emailprocer/
├── app/
│   ├── config/          # Configuration management
│   ├── core/            # Core processing logic
│   ├── integrations/    # External API integrations
│   ├── models/          # Data models
│   ├── services/        # Business logic
│   ├── utils/           # Utility functions
│   └── main.py          # FastAPI application
├── tests/               # Test suite
├── docker/              # Docker configuration
├── scripts/             # Setup and utility scripts
└── docs/                # Documentation
```

### Adding New Integrations

1. Create integration module in `app/integrations/`
2. Add configuration to `app/config/integrations.json`
3. Update settings in `app/config/settings.py`
4. Add tests in `tests/`

---

**Built with ❤️ for efficient IT operations** 