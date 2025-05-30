# EmailBot - Development Guide

**Version**: 1.0  
**Last Updated**: January 2025  
**Team**: Development Team

## 🎯 Development Overview

This guide provides comprehensive information for developers working on EmailBot, including coding standards, development workflow, testing practices, and contribution guidelines.

## 🏗️ Project Architecture

### High-Level Structure
```
emailprocer/
├── app/                    # Main application package
│   ├── config/            # Configuration management
│   ├── core/              # Core business logic
│   ├── integrations/      # External API integrations
│   ├── models/            # Data models and schemas
│   ├── services/          # Business services
│   ├── utils/             # Utility functions
│   └── main.py           # FastAPI application entry point
├── tests/                 # Test suites
├── docs/                  # Documentation
├── docker/                # Docker configurations
├── scripts/               # Utility scripts
└── requirements.txt       # Python dependencies
```

### Key Design Principles

#### 1. Separation of Concerns
- **Models**: Data structures and validation
- **Services**: Business logic and orchestration
- **Integrations**: External API interactions
- **Utils**: Reusable utility functions

#### 2. Dependency Injection
- Use constructor injection for dependencies
- Maintain loose coupling between components
- Enable easy testing with mocks

#### 3. Configuration-Driven
- External configuration via environment variables
- Pydantic settings for type validation
- Environment-specific configurations

#### 4. Error Handling
- Structured error responses
- Comprehensive logging
- Graceful degradation

## 🛠️ Development Environment Setup

### 1. Prerequisites

#### Required Tools
```bash
# Python 3.11+
python --version

# Git
git --version

# Docker (optional)
docker --version

# IDE/Editor (recommended: VS Code, PyCharm)
```

#### Recommended VS Code Extensions
- Python
- Pylance
- Python Docstring Generator
- autoDocstring
- GitLens
- Docker

### 2. Project Setup

```bash
# Clone repository
git clone <repository-url>
cd emailprocer

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Unix/macOS
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### 3. Development Dependencies

Create `requirements-dev.txt`:
```
# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-mock==3.12.0
pytest-cov==4.1.0

# Code quality
black==23.11.0
flake8==6.1.0
mypy==1.7.1
isort==5.12.0

# Documentation
sphinx==7.1.2
sphinx-rtd-theme==1.3.0

# Development tools
pre-commit==3.5.0
jupyter==1.0.0
```

### 4. Pre-commit Hooks

Install pre-commit hooks:
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install
```

Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

## 📝 Coding Standards

### 1. Python Style Guide

#### PEP 8 Compliance
- Follow PEP 8 guidelines
- Line length: 88 characters (Black default)
- Use Black for code formatting
- Use isort for import organization

#### Type Hints
```python
from typing import Optional, List, Dict, Any
from datetime import datetime

def process_email(
    email_id: str, 
    confidence_threshold: float = 85.0
) -> Optional[Dict[str, Any]]:
    """Process email with confidence-based routing."""
    pass

class EmailProcessor:
    def __init__(self, llm_service: LLMService) -> None:
        self.llm_service = llm_service
    
    async def classify_email(self, email: EmailMessage) -> ClassificationResult:
        """Classify email using LLM service."""
        pass
```

#### Docstring Standards
Use Google-style docstrings:
```python
def calculate_confidence_score(
    classification: ClassificationResult, 
    historical_data: List[Dict[str, Any]]
) -> float:
    """Calculate confidence score based on classification and historical data.
    
    Args:
        classification: LLM classification result
        historical_data: Historical accuracy data for similar classifications
        
    Returns:
        Confidence score between 0.0 and 100.0
        
    Raises:
        ValueError: If classification is invalid
        
    Example:
        >>> result = ClassificationResult(category="SUPPORT", confidence=85)
        >>> score = calculate_confidence_score(result, [])
        >>> print(score)
        85.0
    """
    pass
```

### 2. Project Structure Standards

#### File Naming
- Use snake_case for Python files
- Use descriptive names: `email_processor.py`, not `processor.py`
- Test files: `test_email_processor.py`

#### Import Organization
```python
# Standard library imports
import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

# Third-party imports
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai

# Local imports
from app.config.settings import settings
from app.models.email_models import EmailMessage
from app.services.llm_service import LLMService
```

#### Module Structure
```python
"""Module for email processing and classification.

This module contains the core email processing logic including
LLM-based classification and confidence-based routing.
"""

# Module-level constants
DEFAULT_CONFIDENCE_THRESHOLD = 85.0
MAX_RETRY_ATTEMPTS = 3

# Logger setup
logger = logging.getLogger(__name__)

# Class definitions
class EmailProcessor:
    """Email processing and classification service."""
    pass

# Function definitions
async def process_batch(emails: List[EmailMessage]) -> List[ProcessingResult]:
    """Process a batch of emails."""
    pass
```

### 3. Error Handling Standards

#### Exception Hierarchy
```python
class EmailBotError(Exception):
    """Base exception for EmailBot."""
    pass

class ConfigurationError(EmailBotError):
    """Configuration-related errors."""
    pass

class LLMServiceError(EmailBotError):
    """LLM service errors."""
    pass

class M365IntegrationError(EmailBotError):
    """Microsoft 365 integration errors."""
    pass
```

#### Error Handling Patterns
```python
from typing import Union
import logging

logger = logging.getLogger(__name__)

async def safe_api_call(func, *args, **kwargs) -> Union[Dict[str, Any], None]:
    """Safely call external API with error handling."""
    try:
        return await func(*args, **kwargs)
    except httpx.TimeoutException:
        logger.error(f"Timeout calling {func.__name__}")
        return None
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error calling {func.__name__}: {e.response.status_code}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error calling {func.__name__}: {str(e)}")
        return None
```

### 4. Logging Standards

#### Logger Configuration
```python
import logging
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)
```

#### Logging Best Practices
```python
# Include relevant context
logger.info(
    "Email processed successfully",
    email_id=email.id,
    category=classification.category,
    confidence=classification.confidence,
    processing_time_ms=processing_time
)

# Log errors with context
logger.error(
    "Failed to classify email",
    email_id=email.id,
    error_type=type(e).__name__,
    error_message=str(e),
    exc_info=True
)

# Use appropriate log levels
logger.debug("Starting email classification")  # Development info
logger.info("Email processing completed")      # Normal operations
logger.warning("Low confidence classification") # Potential issues
logger.error("API call failed")                # Errors
logger.critical("System unable to start")      # Critical failures
```

## 🧪 Testing Standards

### 1. Test Organization

#### Test Structure
```
tests/
├── unit/                  # Unit tests
│   ├── test_models/
│   ├── test_services/
│   ├── test_core/
│   └── test_utils/
├── integration/           # Integration tests
│   ├── test_m365_integration.py
│   ├── test_llm_integration.py
│   └── test_database.py
├── e2e/                   # End-to-end tests
│   ├── test_email_workflow.py
│   └── test_escalation_workflow.py
├── fixtures/              # Test data and fixtures
└── conftest.py           # Pytest configuration
```

### 2. Unit Testing

#### Test Naming
```python
def test_email_classification_with_high_confidence():
    """Test email classification returns correct category with high confidence."""
    pass

def test_email_classification_with_invalid_input_raises_error():
    """Test email classification raises ValueError for invalid input."""
    pass

def test_confidence_routing_routes_to_automated_response():
    """Test high confidence emails are routed to automated response."""
    pass
```

#### Test Structure (AAA Pattern)
```python
import pytest
from unittest.mock import Mock, AsyncMock
from app.services.email_processor import EmailProcessor
from app.models.email_models import EmailMessage, ClassificationResult

@pytest.mark.asyncio
async def test_process_email_success():
    """Test successful email processing workflow."""
    # Arrange
    mock_llm_service = Mock()
    mock_llm_service.classify_email = AsyncMock(return_value=ClassificationResult(
        category="SUPPORT",
        confidence=92.0,
        reasoning="Technical support request",
        urgency="MEDIUM",
        suggested_action="Provide troubleshooting steps",
        required_expertise=["helpdesk"],
        estimated_effort="15-30 minutes"
    ))
    
    processor = EmailProcessor(llm_service=mock_llm_service)
    email = EmailMessage(
        id="test_123",
        sender_email="user@zgcompanies.com",
        subject="Printer not working",
        body="The printer is showing an error message",
        recipient_email="it-support@zgcompanies.com",
        received_datetime=datetime.utcnow()
    )
    
    # Act
    result = await processor.process_email(email)
    
    # Assert
    assert result.status == "completed"
    assert result.classification.category == "SUPPORT"
    assert result.classification.confidence == 92.0
    mock_llm_service.classify_email.assert_called_once_with(email)
```

### 3. Integration Testing

#### Database Testing
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.models import Base
from app.services.email_service import EmailService

@pytest.fixture
def test_db():
    """Create test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

@pytest.mark.asyncio
async def test_save_processing_result(test_db):
    """Test saving processing result to database."""
    service = EmailService(db_session=test_db)
    
    result = ProcessingResult(
        email_id="test_123",
        status="completed",
        processing_time_ms=1500
    )
    
    saved_result = await service.save_processing_result(result)
    
    assert saved_result.id is not None
    assert saved_result.email_id == "test_123"
```

#### API Testing
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
    assert "components" in data

@pytest.mark.asyncio
async def test_trigger_processing_endpoint():
    """Test manual processing trigger endpoint."""
    response = client.post("/process/trigger")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "triggered"
    assert "timestamp" in data
```

### 4. Test Configuration

#### pytest.ini
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --verbose
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
```

#### conftest.py
```python
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from app.config.settings import Settings
from app.services.llm_service import LLMService

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_settings():
    """Test configuration settings."""
    return Settings(
        debug=True,
        m365_tenant_id="test-tenant",
        m365_client_id="test-client",
        m365_client_secret="test-secret",
        target_mailbox="test@example.com",
        openai_api_key="test-key",
        database_url="sqlite:///:memory:"
    )

@pytest.fixture
def mock_llm_service():
    """Mock LLM service for testing."""
    service = Mock(spec=LLMService)
    service.classify_email = AsyncMock()
    service.generate_response_suggestion = AsyncMock()
    return service
```

## 🔄 Development Workflow

### 1. Git Workflow

#### Branch Strategy
```bash
# Main branches
main              # Production-ready code
develop           # Integration branch for features

# Feature branches
feature/email-processing
feature/teams-integration
feature/pattern-discovery

# Hotfix branches
hotfix/critical-bug-fix

# Release branches
release/v1.1.0
```

#### Commit Message Format
```
type(scope): brief description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Build process or auxiliary tool changes

**Examples:**
```bash
feat(llm): add confidence-based routing logic

Implement routing logic that routes emails based on LLM confidence scores:
- Auto-handle: 85%+ confidence
- Suggest response: 60-84% confidence  
- Human review: 40-59% confidence
- Escalate: <40% confidence

Closes #123

fix(m365): handle token refresh edge case

Fixed issue where token refresh would fail if the token 
expired during a request.

test(email): add integration tests for email processing

Added comprehensive integration tests covering:
- Email fetching from M365
- LLM classification
- Database persistence
```

### 2. Development Process

#### Feature Development
```bash
# 1. Create feature branch
git checkout develop
git pull origin develop
git checkout -b feature/new-feature

# 2. Develop and test
# ... make changes ...
pytest tests/

# 3. Commit changes
git add .
git commit -m "feat(scope): implement new feature"

# 4. Push and create PR
git push origin feature/new-feature
# Create pull request via GitHub/GitLab
```

#### Code Review Process
1. **Self Review**: Review your own code before creating PR
2. **Automated Checks**: Ensure all CI checks pass
3. **Peer Review**: At least one team member review
4. **Testing**: Verify tests pass and coverage is adequate
5. **Merge**: Squash and merge to maintain clean history

### 3. Local Development

#### Running Tests
```bash
# Run all tests
pytest

# Run specific test types
pytest tests/unit/
pytest tests/integration/
pytest -m "not slow"

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/unit/test_email_processor.py::test_process_email_success
```

#### Code Quality Checks
```bash
# Format code
black app/ tests/
isort app/ tests/

# Type checking
mypy app/

# Linting
flake8 app/ tests/

# Run all checks
pre-commit run --all-files
```

#### Running Application
```bash
# Development mode
uvicorn app.main:app --reload --log-level debug

# With environment file
uvicorn app.main:app --reload --env-file .env.dev

# Background processing
python -c "from app.main import process_emails_background; import asyncio; asyncio.run(process_emails_background())"
```

## 📦 Package Management

### 1. Dependency Management

#### Adding Dependencies
```bash
# Install new package
pip install new-package

# Update requirements.txt
pip freeze > requirements.txt

# Or use pip-tools for better dependency management
pip install pip-tools
echo "new-package" >> requirements.in
pip-compile requirements.in
```

#### Security Scanning
```bash
# Install safety
pip install safety

# Check for vulnerabilities
safety check

# Check requirements file
safety check -r requirements.txt
```

### 2. Virtual Environment Management

#### Environment Setup
```bash
# Create environment
python -m venv venv

# Activate
source venv/bin/activate  # Unix/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Deactivate
deactivate
```

## 🔧 Development Tools

### 1. IDE Configuration

#### VS Code settings.json
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.pytestArgs": ["tests"]
}
```

### 2. Debugging

#### VS Code launch.json
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: FastAPI",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/venv/bin/uvicorn",
            "args": ["app.main:app", "--reload"],
            "console": "integratedTerminal",
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            }
        },
        {
            "name": "Python: Test Current File",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["${file}"],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        }
    ]
}
```

#### Debugging Tips
```python
# Use pdb for debugging
import pdb; pdb.set_trace()

# Or ipdb for better interface
import ipdb; ipdb.set_trace()

# Logging for debugging
logger.debug(f"Processing email: {email.id}")
logger.debug(f"Classification result: {classification}")

# Use breakpoints in IDE
# Set breakpoints in VS Code and run with debugger
```

## 📚 Documentation

### 1. Code Documentation

#### Inline Comments
```python
# Calculate confidence adjustment based on historical accuracy
confidence_adjustment = historical_accuracy * 0.1

# Retry with exponential backoff
for attempt in range(max_retries):
    try:
        result = await api_call()
        break
    except Exception:
        wait_time = 2 ** attempt  # Exponential backoff
        await asyncio.sleep(wait_time)
```

#### API Documentation
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class EmailProcessingRequest(BaseModel):
    """Request model for email processing.
    
    Attributes:
        email_id: Unique identifier for the email
        force_reprocess: Whether to reprocess already processed email
    """
    email_id: str
    force_reprocess: bool = False

@app.post("/process/email", response_model=ProcessingResult)
async def process_single_email(request: EmailProcessingRequest):
    """Process a single email through the classification workflow.
    
    Args:
        request: Email processing request parameters
        
    Returns:
        ProcessingResult: Results of the email processing
        
    Raises:
        HTTPException: If email not found or processing fails
    """
    pass
```

### 2. Contributing Guidelines

#### Pull Request Template
```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Test coverage maintained/improved

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Code is commented where necessary
- [ ] Documentation updated
- [ ] No new warnings or errors
```

---

**Document Status**: Active Development  
**Last Updated**: January 2025  
**Maintained By**: Development Team 