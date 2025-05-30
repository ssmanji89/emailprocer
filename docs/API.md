# EmailBot - API Documentation

**Version**: 1.0  
**Base URL**: `http://localhost:8000`  
**API Type**: REST  
**Authentication**: API Key (optional)

## 📖 Overview

EmailBot provides a RESTful API for email processing automation, system monitoring, and configuration management. This document covers all available endpoints with request/response schemas and examples.

## 🔐 Authentication

Authentication is optional for development but recommended for production.

### API Key Authentication
```http
GET /health
X-API-Key: your-api-key-here
```

Configure API key in environment:
```bash
EMAILBOT_API_KEY=your-secret-key
```

## 🏥 Health & Monitoring Endpoints

### GET / - Root Information
Returns basic application information.

**Request:**
```http
GET /
```

**Response:**
```json
{
  "service": "EmailBot",
  "version": "1.0.0",
  "status": "running",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

**Status Codes:**
- `200` - Success

---

### GET /health - System Health Check
Comprehensive health check for all system components.

**Request:**
```http
GET /health
```

**Response:**
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

**Component Status Values:**
- `healthy` - Component functioning normally
- `unhealthy` - Component has issues
- `degraded` - Component partially functional
- `error: {message}` - Component error with details

**Status Codes:**
- `200` - System healthy or degraded
- `500` - System unhealthy

---

### GET /health/detailed - Detailed Health Check
Detailed health information with component-specific data.

**Request:**
```http
GET /health/detailed
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "components": {
    "m365_auth": {
      "status": "healthy",
      "token_valid": true,
      "expires_at": "2024-01-15T11:30:00.000Z",
      "permissions": {
        "Mail.Read": true,
        "Mail.Send": true,
        "Chat.Create": true,
        "ChatMember.ReadWrite": true,
        "User.Read.All": true
      }
    },
    "email_client": {
      "status": "healthy",
      "mailbox": "it-support@zgcompanies.com",
      "display_name": "IT Support",
      "can_read_messages": true,
      "test_timestamp": "2024-01-15T10:30:00.000Z"
    },
    "configuration": {
      "status": "healthy",
      "target_mailbox": "it-support@zgcompanies.com",
      "polling_interval": 5,
      "batch_size": 10,
      "llm_model": "gpt-4",
      "confidence_thresholds": {
        "auto": 85,
        "suggest": 60,
        "review": 40
      }
    }
  }
}
```

**Status Codes:**
- `200` - Success
- `500` - Health check failed

## ⚙️ Configuration Endpoints

### GET /config/validation - Configuration Validation
Validates current system configuration and integrations.

**Request:**
```http
GET /config/validation
```

**Response:**
```json
{
  "status": "valid",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "validations": {
    "m365": {
      "status": "valid",
      "token_valid": true,
      "permissions": {
        "Mail.Read": true,
        "Mail.Send": true,
        "Chat.Create": true,
        "ChatMember.ReadWrite": true,
        "User.Read.All": true
      }
    },
    "email_access": {
      "status": "valid",
      "details": {
        "status": "success",
        "mailbox_display_name": "IT Support",
        "mailbox_email": "it-support@zgcompanies.com",
        "can_read_messages": true,
        "test_timestamp": "2024-01-15T10:30:00.000Z"
      }
    },
    "environment": {
      "status": "valid",
      "missing_variables": []
    }
  }
}
```

**Validation Status Values:**
- `valid` - Configuration is correct
- `invalid` - Configuration has issues
- `error` - Validation failed with error

**Status Codes:**
- `200` - Validation completed
- `500` - Validation failed

## 📧 Email Processing Endpoints

### POST /process/trigger - Trigger Email Processing
Manually trigger email processing workflow.

**Request:**
```http
POST /process/trigger
```

**Response:**
```json
{
  "status": "triggered",
  "message": "Email processing started in background",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

**Status Codes:**
- `200` - Processing triggered successfully
- `500` - Failed to trigger processing

---

### GET /process/status - Processing Status
Get current email processing status and statistics.

**Request:**
```http
GET /process/status
```

**Response:**
```json
{
  "status": "ready",
  "last_processing": "2024-01-15T10:25:00.000Z",
  "emails_processed_today": 45,
  "current_queue_size": 3,
  "processing_stats": {
    "total_processed": 1250,
    "success_rate": 0.98,
    "average_processing_time": 12.5,
    "classification_accuracy": 0.95
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

**Processing Status Values:**
- `ready` - System ready for processing
- `processing` - Currently processing emails
- `error` - Processing encountered errors
- `disabled` - Processing disabled

**Status Codes:**
- `200` - Status retrieved successfully
- `500` - Failed to get status

## 📊 Analytics Endpoints (Future)

### GET /analytics/patterns - Email Patterns
Retrieve discovered email patterns and automation suggestions.

**Request:**
```http
GET /analytics/patterns?days=30&category=all
```

**Query Parameters:**
- `days` (optional) - Number of days to analyze (default: 30)
- `category` (optional) - Filter by email category (default: all)
- `min_frequency` (optional) - Minimum pattern frequency (default: 5)

**Response:**
```json
{
  "analysis_period": {
    "start_date": "2024-01-01T00:00:00.000Z",
    "end_date": "2024-01-15T10:30:00.000Z",
    "total_emails": 450
  },
  "patterns": [
    {
      "pattern_id": "ptn_001",
      "pattern_type": "subject_line",
      "description": "Password reset requests",
      "frequency": 25,
      "automation_potential": 95,
      "sample_subjects": [
        "Password reset request",
        "Need password reset",
        "Forgot password"
      ],
      "suggested_automation": "Automatic password reset instructions"
    }
  ],
  "insights": "25 password reset requests identified as high automation potential",
  "recommendations": [
    "Implement automatic password reset response template",
    "Create self-service password reset link"
  ]
}
```

---

### GET /analytics/performance - Performance Metrics
System performance metrics and trends.

**Request:**
```http
GET /analytics/performance?period=week
```

**Query Parameters:**
- `period` - Analysis period: `day`, `week`, `month` (default: week)

**Response:**
```json
{
  "period": "week",
  "metrics": {
    "emails_processed": 315,
    "average_processing_time": 12.3,
    "classification_accuracy": 0.96,
    "automation_rate": 0.89,
    "escalation_rate": 0.11
  },
  "trends": {
    "processing_time": "decreasing",
    "accuracy": "stable",
    "volume": "increasing"
  },
  "performance_goals": {
    "processing_time_target": 30,
    "accuracy_target": 0.95,
    "automation_target": 0.90
  }
}
```

## 🔧 Management Endpoints (Future)

### GET /emails - Email History
Retrieve processed email history with filtering options.

**Request:**
```http
GET /emails?limit=50&category=SUPPORT&status=completed
```

**Query Parameters:**
- `limit` (optional) - Number of emails to return (default: 50, max: 200)
- `offset` (optional) - Pagination offset (default: 0)
- `category` (optional) - Filter by category
- `status` (optional) - Filter by processing status
- `date_from` (optional) - Start date filter (ISO 8601)
- `date_to` (optional) - End date filter (ISO 8601)
- `sender` (optional) - Filter by sender email

**Response:**
```json
{
  "total": 1250,
  "limit": 50,
  "offset": 0,
  "emails": [
    {
      "id": "email_123",
      "sender_email": "user@zgcompanies.com",
      "subject": "Printer not working",
      "received_datetime": "2024-01-15T09:30:00.000Z",
      "processed_datetime": "2024-01-15T09:30:15.000Z",
      "classification": {
        "category": "SUPPORT",
        "confidence": 92,
        "reasoning": "Technical issue with office equipment",
        "urgency": "MEDIUM"
      },
      "processing_result": {
        "status": "completed",
        "action_taken": "automated_response",
        "response_sent": true,
        "escalation_id": null,
        "processing_time_ms": 2150
      }
    }
  ]
}
```

---

### GET /emails/{email_id} - Email Details
Get detailed information for a specific email.

**Request:**
```http
GET /emails/email_123
```

**Response:**
```json
{
  "id": "email_123",
  "sender_email": "user@zgcompanies.com",
  "sender_name": "John Doe",
  "recipient_email": "it-support@zgcompanies.com",
  "subject": "Printer not working",
  "body": "Hi, the printer in conference room A is not working. It shows a paper jam error but I don't see any jammed paper. Can someone help?",
  "received_datetime": "2024-01-15T09:30:00.000Z",
  "processed_datetime": "2024-01-15T09:30:15.000Z",
  "attachments": [],
  "classification": {
    "category": "SUPPORT",
    "confidence": 92,
    "reasoning": "Technical issue with office equipment requiring IT support",
    "urgency": "MEDIUM",
    "suggested_action": "Provide printer troubleshooting steps",
    "required_expertise": ["helpdesk", "hardware_support"],
    "estimated_effort": "15-30 minutes"
  },
  "processing_result": {
    "status": "completed",
    "action_taken": "automated_response",
    "response_sent": true,
    "escalation_id": null,
    "processing_time_ms": 2150,
    "error_message": null
  },
  "automated_response": {
    "content": "Thank you for reporting the printer issue. Please try the following steps: 1) Turn off the printer, 2) Check for paper jams in all trays, 3) Turn on the printer. If the issue persists, please contact IT at ext. 1234.",
    "sent_at": "2024-01-15T09:30:20.000Z"
  }
}
```

---

### GET /escalations - Escalation History
Retrieve Teams escalation history and status.

**Request:**
```http
GET /escalations?status=active&limit=20
```

**Query Parameters:**
- `status` (optional) - Filter by status: `active`, `resolved`, `all`
- `limit` (optional) - Number of escalations to return
- `email_category` (optional) - Filter by original email category

**Response:**
```json
{
  "total": 15,
  "escalations": [
    {
      "team_id": "19:meeting_abc123",
      "email_id": "email_456",
      "team_name": "IT-ESCALATION-2024-01-15-server-outage",
      "created_at": "2024-01-15T08:45:00.000Z",
      "resolved_at": null,
      "status": "active",
      "members": [
        "it-admin@zgcompanies.com",
        "system-admin@zgcompanies.com",
        "network-admin@zgcompanies.com"
      ],
      "original_email": {
        "sender": "manager@zgcompanies.com",
        "subject": "Critical: Email server down",
        "category": "ESCALATION",
        "urgency": "CRITICAL"
      },
      "resolution_notes": null,
      "sla_status": "within_target"
    }
  ]
}
```

## 🔧 Administrative Endpoints (Future)

### PUT /config/settings - Update Configuration
Update system configuration settings.

**Request:**
```http
PUT /config/settings
Content-Type: application/json

{
  "confidence_threshold_auto": 90,
  "confidence_threshold_suggest": 65,
  "polling_interval_minutes": 3,
  "teams_default_members": ["admin@zgcompanies.com", "it-manager@zgcompanies.com"]
}
```

**Response:**
```json
{
  "status": "updated",
  "message": "Configuration updated successfully",
  "updated_settings": {
    "confidence_threshold_auto": 90,
    "confidence_threshold_suggest": 65,
    "polling_interval_minutes": 3,
    "teams_default_members": ["admin@zgcompanies.com", "it-manager@zgcompanies.com"]
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

---

### POST /processing/rules - Add Processing Rule
Add custom email processing rule.

**Request:**
```http
POST /processing/rules
Content-Type: application/json

{
  "name": "Auto-respond to password resets",
  "conditions": {
    "subject_contains": ["password", "reset"],
    "sender_domain": "zgcompanies.com"
  },
  "actions": {
    "auto_respond": true,
    "response_template": "password_reset_instructions",
    "mark_as_handled": true
  },
  "enabled": true
}
```

**Response:**
```json
{
  "rule_id": "rule_001",
  "status": "created",
  "message": "Processing rule created successfully",
  "rule": {
    "id": "rule_001",
    "name": "Auto-respond to password resets",
    "conditions": {
      "subject_contains": ["password", "reset"],
      "sender_domain": "zgcompanies.com"
    },
    "actions": {
      "auto_respond": true,
      "response_template": "password_reset_instructions",
      "mark_as_handled": true
    },
    "enabled": true,
    "created_at": "2024-01-15T10:30:00.000Z"
  }
}
```

## 📊 Data Models

### Email Classification Result
```json
{
  "category": "PURCHASING|SUPPORT|INFORMATION|ESCALATION|CONSULTATION",
  "confidence": 85.5,
  "reasoning": "String explaining classification decision",
  "urgency": "LOW|MEDIUM|HIGH|CRITICAL",
  "suggested_action": "Specific recommended action",
  "required_expertise": ["list", "of", "skills"],
  "estimated_effort": "Time estimate string"
}
```

### Processing Result
```json
{
  "email_id": "unique_email_identifier",
  "status": "received|classifying|analyzing|routing|responding|escalating|completed|failed",
  "classification": "ClassificationResult object",
  "action_taken": "Description of action taken",
  "escalation_id": "Teams group ID if escalated",
  "response_sent": true,
  "processing_time_ms": 2150,
  "error_message": "Error details if failed",
  "created_at": "2024-01-15T10:30:00.000Z",
  "updated_at": "2024-01-15T10:30:00.000Z"
}
```

## ❌ Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": "Additional error details",
    "timestamp": "2024-01-15T10:30:00.000Z",
    "request_id": "req_123456"
  }
}
```

### Common Error Codes
- `INVALID_REQUEST` - Malformed request
- `AUTHENTICATION_FAILED` - Invalid API key
- `AUTHORIZATION_FAILED` - Insufficient permissions
- `RESOURCE_NOT_FOUND` - Requested resource not found
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `INTERNAL_ERROR` - Server error
- `SERVICE_UNAVAILABLE` - External service down
- `CONFIGURATION_ERROR` - System misconfiguration

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Too Many Requests
- `500` - Internal Server Error
- `502` - Bad Gateway
- `503` - Service Unavailable

## 📈 Rate Limiting

### Default Limits
- **Health endpoints**: 60 requests/minute
- **Processing endpoints**: 10 requests/minute
- **Analytics endpoints**: 30 requests/minute
- **Administrative endpoints**: 20 requests/minute

### Rate Limit Headers
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642252800
```

## 🔧 Development & Testing

### API Testing with curl
```bash
# Health check
curl http://localhost:8000/health

# Trigger processing
curl -X POST http://localhost:8000/process/trigger

# Get processing status
curl http://localhost:8000/process/status

# Configuration validation
curl http://localhost:8000/config/validation
```

### Python Client Example
```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Trigger processing
response = requests.post("http://localhost:8000/process/trigger")
print(response.json())
```

### Interactive API Documentation
When the application is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

**API Version**: 1.0  
**Last Updated**: January 2025  
**Support**: See README.md for support information 