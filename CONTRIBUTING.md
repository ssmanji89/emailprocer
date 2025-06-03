# Contributing to EmailBot

Thank you for your interest in contributing to EmailBot! This document provides guidelines for contributing to our open source AI-powered email classification system.

## 🤝 How to Contribute

### Types of Contributions

We welcome various types of contributions:

- **Bug Reports**: Help us identify and fix issues
- **Feature Requests**: Suggest new functionality
- **Code Contributions**: Submit bug fixes and new features
- **Documentation**: Improve our documentation
- **Testing**: Help with testing and quality assurance
- **Security**: Report security vulnerabilities responsibly

## 🚀 Getting Started

### Prerequisites

1. **Development Environment**: Set up your local development environment following our [SETUP.md](SETUP.md) guide
2. **GitHub Account**: Create a GitHub account if you don't have one
3. **Git Knowledge**: Basic understanding of Git and GitHub workflows

### First Time Setup

```bash
# 1. Fork the repository on GitHub
# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/emailprocer.git
cd emailprocer

# 3. Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/emailprocer.git

# 4. Set up development environment
cp env.example .env
# Edit .env with your test credentials (never commit these!)

# 5. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 6. Install pre-commit hooks
pre-commit install

# 7. Run tests to verify setup
python -m pytest
```

## 📝 Development Guidelines

### Code Standards

#### Python Code Style
- **PEP 8**: Follow Python style guidelines
- **Type Hints**: Use type annotations for all functions
- **Docstrings**: Document all public functions and classes
- **Maximum Line Length**: 88 characters (Black formatter)

```python
from typing import List, Optional
import asyncio

async def process_emails(
    mailbox: str, 
    batch_size: int = 10
) -> List[EmailResult]:
    """
    Process emails from the specified mailbox.
    
    Args:
        mailbox: Email address of the mailbox to process
        batch_size: Number of emails to process in each batch
        
    Returns:
        List of email processing results
        
    Raises:
        EmailProcessingError: If email processing fails
    """
    # Implementation here
    pass
```

#### Frontend Code Style (TypeScript/React)
- **TypeScript**: Use strict type checking
- **ESLint**: Follow configured linting rules
- **Prettier**: Use consistent code formatting
- **Component Structure**: Follow established patterns

```typescript
interface EmailListProps {
  emails: Email[]
  onEmailSelect: (email: Email) => void
  isLoading?: boolean
}

export function EmailList({ 
  emails, 
  onEmailSelect, 
  isLoading = false 
}: EmailListProps): JSX.Element {
  // Implementation here
}
```

### Security Guidelines

#### Sensitive Data Handling
- **Never commit credentials**: Always use environment variables
- **Sanitize test data**: Remove personal information from test cases
- **Validate inputs**: Implement proper input validation
- **Encrypt sensitive data**: Use appropriate encryption for stored data

#### Example: Sanitizing Test Data
```python
# ❌ Don't do this
test_email = "john.doe@realcompany.com"

# ✅ Do this instead
test_email = "testuser@example.com"
```

### Testing Requirements

#### Test Coverage
- **Minimum 80%**: Maintain at least 80% code coverage
- **Unit Tests**: Test individual functions and methods
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete workflows

#### Test Structure
```python
import pytest
from unittest.mock import AsyncMock, patch

class TestEmailProcessor:
    """Test cases for email processing functionality."""
    
    @pytest.fixture
    def mock_email_data(self):
        """Provide sanitized test email data."""
        return {
            "from": "testuser@example.com",
            "subject": "Test email subject",
            "body": "Test email body content"
        }
    
    async def test_process_email_success(self, mock_email_data):
        """Test successful email processing."""
        # Test implementation
        pass
        
    async def test_process_email_failure(self):
        """Test email processing error handling."""
        # Test implementation
        pass
```

## 🔄 Contribution Workflow

### Step 1: Create an Issue
Before starting work, create or comment on an issue to:
- Describe the problem or feature
- Discuss the approach
- Get feedback from maintainers

### Step 2: Create a Branch
```bash
# Update your fork
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### Step 3: Make Changes
- Write code following our guidelines
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### Step 4: Commit Changes
```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add email classification retry logic

- Implement exponential backoff for API failures
- Add unit tests for retry mechanism  
- Update documentation for new retry configuration

Closes #123"
```

#### Commit Message Format
```
type(scope): brief description

- Detailed explanation of changes
- List any breaking changes
- Reference issues (Closes #123)

Types: feat, fix, docs, style, refactor, test, chore
```

### Step 5: Submit Pull Request
```bash
# Push branch to your fork
git push origin feature/your-feature-name

# Create pull request on GitHub
# Include description, testing notes, and related issues
```

## 📋 Pull Request Guidelines

### PR Requirements
- [ ] **Clear Description**: Explain what changes were made and why
- [ ] **Issue Reference**: Link to related issue(s)
- [ ] **Tests Added**: Include tests for new functionality
- [ ] **Documentation Updated**: Update relevant documentation
- [ ] **Security Check**: No sensitive data in code or tests
- [ ] **Breaking Changes**: Clearly document any breaking changes

### PR Template
```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] No sensitive data included
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=app

# Run specific test file
python -m pytest tests/test_email_processor.py

# Run frontend tests
cd dashboard && npm test
```

### Test Data Guidelines
- **Use realistic but fake data**: Create believable test scenarios
- **Anonymize everything**: Never use real emails, names, or company data
- **Consistent test data**: Use the same test patterns across the codebase

## 📚 Documentation

### Documentation Types
- **Code Comments**: Explain complex logic
- **API Documentation**: Document all endpoints
- **User Guides**: Help users understand features
- **Developer Guides**: Help contributors understand architecture

### Documentation Standards
- **Clear and Concise**: Write for your audience
- **Examples Included**: Provide code examples
- **Up to Date**: Keep documentation current with code changes
- **Security Focused**: Include security considerations

## 🔍 Code Review Process

### Review Checklist
- **Functionality**: Does the code work as intended?
- **Security**: Are there any security vulnerabilities?
- **Performance**: Are there any performance issues?
- **Maintainability**: Is the code clean and well-structured?
- **Tests**: Are tests comprehensive and passing?

### Addressing Feedback
- **Be Responsive**: Address feedback promptly
- **Ask Questions**: Clarify feedback if needed
- **Make Changes**: Update code based on review comments
- **Be Professional**: Maintain a positive, collaborative attitude

## 🏆 Recognition

### Contributor Recognition
- **Contributors File**: All contributors are listed in CONTRIBUTORS.md
- **Release Notes**: Significant contributions are mentioned in releases
- **Special Recognition**: Outstanding contributions may receive special recognition

## 📞 Getting Help

### Community Resources
- **GitHub Discussions**: Ask questions and discuss ideas
- **Issues**: Report bugs and request features
- **Documentation**: Comprehensive guides and API docs

### Contact
- **General Questions**: Create a GitHub discussion
- **Bug Reports**: Create a GitHub issue
- **Security Issues**: Email security@emailbot-project.org
- **Feature Requests**: Create a GitHub issue with feature request template

## 🚫 What Not to Contribute

### Avoid Contributing
- **Real credentials or API keys**: Never include actual secrets
- **Personal or company data**: Use only sanitized test data
- **Copyright violations**: Only contribute original or properly licensed code
- **Malicious code**: Any code intended to harm users or systems
- **Spam or low-quality content**: Ensure contributions add value

## 📄 License

By contributing to EmailBot, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to EmailBot! Your efforts help make email management better for everyone. 🚀 