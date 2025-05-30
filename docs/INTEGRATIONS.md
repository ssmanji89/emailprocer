# EmailBot - Integrations Guide

**Version**: 1.0  
**Last Updated**: January 2025  
**Purpose**: Complete setup guide for M365, CRM, and database integrations

## 🎯 Integration Overview

This guide provides step-by-step instructions for setting up all external integrations required for EmailBot, including Microsoft 365, CRM systems, databases, and webhook endpoints.

## 🔐 Microsoft 365 Integration Setup

### App Registration Requirements

#### 1. Create Azure App Registration
```bash
# Using Azure CLI
az ad app create \
  --display-name "EmailBot-Production" \
  --sign-in-audience "AzureADMyOrg" \
  --required-resource-accesses @app-permissions.json
```

#### 2. Required API Permissions
Create `app-permissions.json`:
```json
[
  {
    "resourceAppId": "00000003-0000-0000-c000-000000000000",
    "resourceAccess": [
      {
        "id": "810c84a8-4a9e-49e0-bf33-d2c4e8e7f4b0",
        "type": "Role"
      },
      {
        "id": "b633e1c5-b582-4048-a93e-9f11b44c7e96",
        "type": "Role"
      },
      {
        "id": "9b8d1f7f-1d5a-4b8e-9f1b-3c7e8d9f2a1b",
        "type": "Role"
      },
      {
        "id": "df021288-bdef-4463-88db-98f22de89214",
        "type": "Role"
      },
      {
        "id": "6e472fd1-ad78-48da-a0f0-97ab2c6b769e",
        "type": "Role"
      }
    ]
  }
]
```

#### 3. Permission Details
| Permission | Type | Purpose |
|------------|------|---------|
| `Mail.Read` | Application | Read emails from shared mailbox |
| `Mail.Send` | Application | Send automated responses |
| `Chat.Create` | Application | Create Teams escalation groups |
| `ChatMember.ReadWrite` | Application | Manage Teams group membership |
| `User.Read.All` | Application | Read user profiles for team assembly |

### Authentication Configuration

#### Environment Variables
```bash
# M365 Configuration
EMAILBOT_M365_TENANT_ID=your-tenant-id-here
EMAILBOT_M365_CLIENT_ID=your-client-id-here
EMAILBOT_M365_CLIENT_SECRET=your-client-secret-here
EMAILBOT_TARGET_MAILBOX=it-support@zgcompanies.com

# Graph API Settings
EMAILBOT_M365_AUTHORITY=https://login.microsoftonline.com/your-tenant-id
EMAILBOT_M365_SCOPE=https://graph.microsoft.com/.default
```

#### Token Management Implementation
```python
from msal import ConfidentialClientApplication
import redis
import json
from datetime import datetime, timedelta

class GraphAuthManager:
    """Microsoft Graph authentication with token caching."""
    
    def __init__(self, tenant_id: str, client_id: str, client_secret: str, redis_client=None):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.redis = redis_client
        
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.scope = ["https://graph.microsoft.com/.default"]
        
        self.app = ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=self.authority
        )
    
    async def get_access_token(self) -> str:
        """Get valid access token with caching."""
        cache_key = f"emailbot:token:{self.client_id}"
        
        # Check cache first
        if self.redis:
            cached_token = await self.redis.get(cache_key)
            if cached_token:
                token_data = json.loads(cached_token)
                if datetime.fromisoformat(token_data['expires_at']) > datetime.utcnow():
                    return token_data['access_token']
        
        # Get new token
        result = self.app.acquire_token_for_client(scopes=self.scope)
        
        if "access_token" not in result:
            raise AuthenticationError(f"Failed to acquire token: {result.get('error_description')}")
        
        # Cache token
        if self.redis:
            expires_at = datetime.utcnow() + timedelta(seconds=result['expires_in'] - 60)
            token_data = {
                'access_token': result['access_token'],
                'expires_at': expires_at.isoformat()
            }
            await self.redis.setex(
                cache_key, 
                result['expires_in'] - 60, 
                json.dumps(token_data)
            )
        
        return result['access_token']
```

### Permission Validation Script
```python
async def validate_m365_permissions() -> Dict[str, bool]:
    """Validate all required M365 permissions."""
    auth_manager = GraphAuthManager(...)
    token = await auth_manager.get_access_token()
    
    headers = {"Authorization": f"Bearer {token}"}
    
    validations = {}
    
    # Test Mail.Read
    try:
        response = await httpx.get(
            f"https://graph.microsoft.com/v1.0/users/{MAILBOX}/messages",
            headers=headers,
            params={"$top": 1}
        )
        validations["Mail.Read"] = response.status_code == 200
    except:
        validations["Mail.Read"] = False
    
    # Test Mail.Send
    try:
        # Test send capability (dry run)
        test_message = {
            "message": {
                "subject": "EmailBot Permission Test",
                "body": {"contentType": "Text", "content": "Test"},
                "toRecipients": [{"emailAddress": {"address": MAILBOX}}]
            },
            "saveToSentItems": False
        }
        response = await httpx.post(
            f"https://graph.microsoft.com/v1.0/users/{MAILBOX}/sendMail",
            headers=headers,
            json=test_message
        )
        validations["Mail.Send"] = response.status_code in [200, 202]
    except:
        validations["Mail.Send"] = False
    
    # Test Chat.Create
    try:
        response = await httpx.get(
            "https://graph.microsoft.com/v1.0/me/chats",
            headers=headers,
            params={"$top": 1}
        )
        validations["Chat.Create"] = response.status_code == 200
    except:
        validations["Chat.Create"] = False
    
    return validations
```

## 🔗 CRM Integration Configuration

### Salesforce Integration

#### 1. OAuth2 Setup
```python
SALESFORCE_CONFIG = {
    "name": "salesforce",
    "enabled": True,
    "priority": 1,
    "authentication": {
        "type": "oauth2",
        "client_id": "${SALESFORCE_CLIENT_ID}",
        "client_secret": "${SALESFORCE_CLIENT_SECRET}",
        "token_url": "https://login.salesforce.com/services/oauth2/token",
        "scope": "api"
    },
    "api_config": {
        "base_url": "https://yourinstance.salesforce.com",
        "version": "v58.0",
        "timeout": 30,
        "retry_attempts": 3
    }
}
```

#### 2. Implementation
```python
class SalesforceClient:
    """Salesforce CRM integration client."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session = httpx.AsyncClient()
        self.access_token = None
        self.token_expires = None
    
    async def authenticate(self) -> bool:
        """Authenticate with Salesforce OAuth2."""
        auth_data = {
            "grant_type": "client_credentials",
            "client_id": self.config["authentication"]["client_id"],
            "client_secret": self.config["authentication"]["client_secret"]
        }
        
        response = await self.session.post(
            self.config["authentication"]["token_url"],
            data=auth_data
        )
        
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.token_expires = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
            return True
        return False
    
    async def search_contact(self, email: str) -> Optional[Dict[str, Any]]:
        """Search for contact by email address."""
        if not await self._ensure_authenticated():
            return None
        
        query = f"FIND '{email}' IN EMAIL FIELDS RETURNING Contact(Id, Name, Email, Phone)"
        
        response = await self.session.get(
            f"{self.config['api_config']['base_url']}/services/data/{self.config['api_config']['version']}/search/",
            headers={"Authorization": f"Bearer {self.access_token}"},
            params={"q": query}
        )
        
        if response.status_code == 200:
            results = response.json()
            if results.get("searchRecords"):
                return results["searchRecords"][0]
        return None
    
    async def create_case(self, email_data: Dict[str, Any]) -> Optional[str]:
        """Create support case from email."""
        case_data = {
            "Subject": email_data["subject"],
            "Description": email_data["body"],
            "Origin": "Email",
            "Status": "New",
            "Priority": self._map_urgency_to_priority(email_data.get("urgency", "MEDIUM"))
        }
        
        response = await self.session.post(
            f"{self.config['api_config']['base_url']}/services/data/{self.config['api_config']['version']}/sobjects/Case/",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            },
            json=case_data
        )
        
        if response.status_code == 201:
            return response.json()["id"]
        return None
```

### HubSpot Integration

#### Configuration
```python
HUBSPOT_CONFIG = {
    "name": "hubspot",
    "enabled": True,
    "priority": 2,
    "authentication": {
        "type": "api_key",
        "api_key": "${HUBSPOT_API_KEY}"
    },
    "api_config": {
        "base_url": "https://api.hubapi.com",
        "timeout": 30,
        "retry_attempts": 3
    },
    "operations": {
        "search_contact": {
            "endpoint": "/crm/v3/objects/contacts/search",
            "method": "POST"
        },
        "create_ticket": {
            "endpoint": "/crm/v3/objects/tickets",
            "method": "POST"
        }
    }
}
```

## 🗄️ Database Integration Setup

### PostgreSQL Customer Database

#### 1. Connection Configuration
```python
DATABASE_CONFIG = {
    "name": "customer_db",
    "enabled": True,
    "type": "postgresql",
    "connection": {
        "host": "${DB_HOST}",
        "port": 5432,
        "database": "${DB_NAME}",
        "username": "${DB_USER}",
        "password": "${DB_PASSWORD}",
        "ssl_mode": "require"
    },
    "pool_config": {
        "min_connections": 5,
        "max_connections": 20,
        "command_timeout": 30
    }
}
```

#### 2. Database Client Implementation
```python
import asyncpg
from typing import List, Dict, Any, Optional

class DatabaseConnector:
    """Generic database connector for customer data."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pool = None
    
    async def initialize(self):
        """Initialize connection pool."""
        connection_string = self._build_connection_string()
        
        self.pool = await asyncpg.create_pool(
            connection_string,
            min_size=self.config["pool_config"]["min_connections"],
            max_size=self.config["pool_config"]["max_connections"],
            command_timeout=self.config["pool_config"]["command_timeout"]
        )
    
    async def find_customer(self, email: str) -> Optional[Dict[str, Any]]:
        """Find customer by email address."""
        async with self.pool.acquire() as conn:
            query = "SELECT * FROM customers WHERE email = $1"
            row = await conn.fetchrow(query, email)
            return dict(row) if row else None
    
    async def get_support_history(self, email: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get customer support ticket history."""
        async with self.pool.acquire() as conn:
            query = """
                SELECT ticket_id, subject, status, created_at, resolved_at 
                FROM support_tickets 
                WHERE customer_email = $1 
                ORDER BY created_at DESC 
                LIMIT $2
            """
            rows = await conn.fetch(query, email, limit)
            return [dict(row) for row in rows]
    
    async def create_support_ticket(self, ticket_data: Dict[str, Any]) -> str:
        """Create new support ticket."""
        async with self.pool.acquire() as conn:
            query = """
                INSERT INTO support_tickets (customer_email, subject, description, priority, created_at)
                VALUES ($1, $2, $3, $4, NOW())
                RETURNING ticket_id
            """
            ticket_id = await conn.fetchval(
                query, 
                ticket_data["email"],
                ticket_data["subject"],
                ticket_data["description"],
                ticket_data["priority"]
            )
            return str(ticket_id)
```

### Query Templates

#### Customer Lookup Queries
```sql
-- Standard customer lookup
SELECT 
    customer_id,
    email,
    first_name,
    last_name,
    company,
    phone,
    support_tier,
    created_at
FROM customers 
WHERE email = $1;

-- Customer with contract info
SELECT 
    c.*,
    ct.contract_type,
    ct.support_level,
    ct.expiry_date
FROM customers c
LEFT JOIN contracts ct ON c.customer_id = ct.customer_id
WHERE c.email = $1 AND ct.status = 'active';

-- Support ticket history
SELECT 
    ticket_id,
    subject,
    description,
    priority,
    status,
    created_at,
    resolved_at,
    assigned_to
FROM support_tickets 
WHERE customer_email = $1 
ORDER BY created_at DESC 
LIMIT $2;
```

## 🔗 Integration Gateway Implementation

### Generic Integration Gateway
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class IntegrationGateway(ABC):
    """Abstract base class for external integrations."""
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with external service."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test connection to external service."""
        pass
    
    @abstractmethod
    async def search_contact(self, email: str) -> Optional[Dict[str, Any]]:
        """Search for contact by email."""
        pass

class CRMGateway:
    """Gateway for CRM system integrations."""
    
    def __init__(self, config_manager: ConfigurationManager):
        self.config_manager = config_manager
        self.integrations = {}
    
    async def initialize(self):
        """Initialize all enabled CRM integrations."""
        crm_configs = await self.config_manager.load_integration_config("crm_systems")
        
        for config in crm_configs:
            if config["name"] == "salesforce":
                self.integrations["salesforce"] = SalesforceClient(config)
            elif config["name"] == "hubspot":
                self.integrations["hubspot"] = HubSpotClient(config)
            
            # Test authentication
            if config["name"] in self.integrations:
                success = await self.integrations[config["name"]].authenticate()
                if not success:
                    logger.warning(f"Failed to authenticate with {config['name']}")
    
    async def enrich_email_context(self, email: EmailMessage) -> Dict[str, Any]:
        """Enrich email with CRM context."""
        context = {}
        
        for name, client in self.integrations.items():
            try:
                contact = await client.search_contact(email.sender_email)
                if contact:
                    context[f"{name}_contact"] = contact
                    
                # Get additional context based on contact
                if hasattr(client, 'get_account_info') and contact:
                    account = await client.get_account_info(contact.get('AccountId'))
                    if account:
                        context[f"{name}_account"] = account
                        
            except Exception as e:
                logger.warning(f"Failed to get context from {name}: {str(e)}")
        
        return context
```

## 🔌 Webhook Integration

### Real-time Email Processing

#### Webhook Configuration
```python
WEBHOOK_CONFIG = {
    "name": "real_time_processing",
    "enabled": False,
    "url": "/webhooks/email",
    "authentication": {
        "type": "bearer_token",
        "token": "${WEBHOOK_TOKEN}"
    },
    "filters": {
        "sender_domains": ["zgcompanies.com"],
        "subjects_containing": ["urgent", "critical", "down", "outage"]
    },
    "processing": {
        "immediate": True,
        "bypass_batch": True,
        "priority": "HIGH"
    }
}
```

#### Webhook Endpoint Implementation
```python
from fastapi import HTTPException, Depends, Header
from typing import Optional

async def verify_webhook_token(authorization: Optional[str] = Header(None)):
    """Verify webhook authentication token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    token = authorization.replace("Bearer ", "")
    expected_token = settings.webhook_token
    
    if token != expected_token:
        raise HTTPException(status_code=401, detail="Invalid webhook token")
    
    return True

@app.post("/webhooks/email")
async def webhook_email_received(
    webhook_data: WebhookEmailData,
    authenticated: bool = Depends(verify_webhook_token)
):
    """Handle real-time email webhook."""
    try:
        # Validate webhook data
        email = EmailMessage.from_webhook(webhook_data)
        
        # Apply filters
        if not await apply_webhook_filters(email):
            return {"status": "filtered", "message": "Email does not match filters"}
        
        # Process immediately
        processing_result = await email_processor.process_email(email)
        
        return {
            "status": "processed",
            "email_id": email.id,
            "classification": processing_result.classification.category,
            "confidence": processing_result.classification.confidence,
            "action_taken": processing_result.action_taken
        }
        
    except Exception as e:
        logger.error(f"Webhook processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Processing failed")

async def apply_webhook_filters(email: EmailMessage) -> bool:
    """Apply webhook filters to determine if email should be processed."""
    config = await config_manager.load_integration_config("webhook_endpoints")
    
    if not config:
        return False
    
    webhook_config = config[0]  # Assuming single webhook config
    filters = webhook_config.get("filters", {})
    
    # Check sender domain
    sender_domains = filters.get("sender_domains", [])
    if sender_domains:
        email_domain = email.sender_email.split("@")[1]
        if email_domain not in sender_domains:
            return False
    
    # Check subject keywords
    subject_keywords = filters.get("subjects_containing", [])
    if subject_keywords:
        subject_lower = email.subject.lower()
        if not any(keyword.lower() in subject_lower for keyword in subject_keywords):
            return False
    
    return True
```

## ⚙️ Configuration Management

### Dynamic Configuration Loading
```python
class IntegrationConfigManager:
    """Manage dynamic integration configurations."""
    
    def __init__(self, config_file: str = "app/config/integrations.json"):
        self.config_file = config_file
        self.config_cache = {}
        self.last_reload = None
        self.reload_interval = 300  # 5 minutes
        self.watchers = {}
    
    async def load_config(self) -> Dict[str, Any]:
        """Load configuration from file with caching."""
        current_time = time.time()
        
        # Check if reload is needed
        if (self.last_reload is None or 
            current_time - self.last_reload > self.reload_interval):
            await self._reload_config()
        
        return self.config_cache
    
    async def _reload_config(self):
        """Reload configuration from file."""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Validate configuration
            await self._validate_config(config)
            
            # Update cache
            self.config_cache = config
            self.last_reload = time.time()
            
            logger.info("Configuration reloaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to reload configuration: {str(e)}")
            raise ConfigurationError(f"Configuration reload failed: {str(e)}")
    
    async def update_integration_status(self, integration_name: str, enabled: bool):
        """Dynamically enable/disable integration."""
        config = await self.load_config()
        
        # Update CRM systems
        for crm in config.get("crm_systems", []):
            if crm["name"] == integration_name:
                crm["enabled"] = enabled
                break
        
        # Update databases
        for db in config.get("databases", []):
            if db["name"] == integration_name:
                db["enabled"] = enabled
                break
        
        # Save updated configuration
        await self._save_config(config)
        
        # Trigger reload
        self.last_reload = None
    
    async def validate_all_integrations(self) -> Dict[str, ValidationResult]:
        """Validate all configured integrations."""
        config = await self.load_config()
        results = {}
        
        # Validate CRM systems
        for crm_config in config.get("crm_systems", []):
            if crm_config.get("enabled", False):
                result = await self._validate_crm_integration(crm_config)
                results[crm_config["name"]] = result
        
        # Validate databases
        for db_config in config.get("databases", []):
            if db_config.get("enabled", False):
                result = await self._validate_database_integration(db_config)
                results[db_config["name"]] = result
        
        return results
```

### Environment Variable Templates

#### Complete Environment Configuration
```bash
# Application Settings
EMAILBOT_DEBUG=false
EMAILBOT_LOG_LEVEL=INFO
EMAILBOT_HOST=0.0.0.0
EMAILBOT_PORT=8000

# Microsoft 365 Integration
EMAILBOT_M365_TENANT_ID=your-tenant-id
EMAILBOT_M365_CLIENT_ID=your-client-id
EMAILBOT_M365_CLIENT_SECRET=your-client-secret
EMAILBOT_TARGET_MAILBOX=it-support@zgcompanies.com

# OpenAI Configuration
EMAILBOT_OPENAI_API_KEY=your-openai-api-key
EMAILBOT_OPENAI_MODEL=gpt-4
EMAILBOT_OPENAI_MAX_TOKENS=500
EMAILBOT_OPENAI_TEMPERATURE=0.1

# Database Configuration
EMAILBOT_DATABASE_URL=postgresql://user:password@localhost:5432/emailbot
EMAILBOT_REDIS_URL=redis://localhost:6379/0

# CRM Integrations
SALESFORCE_CLIENT_ID=your-salesforce-client-id
SALESFORCE_CLIENT_SECRET=your-salesforce-client-secret
SALESFORCE_INSTANCE_URL=https://yourinstance.salesforce.com

HUBSPOT_API_KEY=your-hubspot-api-key

# External Database
DB_HOST=customer-db.company.com
DB_NAME=customer_data
DB_USER=emailbot_user
DB_PASSWORD=secure_password

# Security
EMAILBOT_API_KEY=your-secure-api-key
EMAILBOT_ENCRYPTION_KEY=your-encryption-key
WEBHOOK_TOKEN=your-webhook-token

# Performance Tuning
EMAILBOT_POLLING_INTERVAL_MINUTES=5
EMAILBOT_BATCH_SIZE=20
EMAILBOT_MAX_RETRIES=3
EMAILBOT_REQUEST_TIMEOUT=30

# Monitoring
EMAILBOT_METRICS_ENABLED=true
EMAILBOT_HEALTH_CHECK_INTERVAL=60
```

## 🧪 Integration Testing

### Automated Testing Suite
```python
import pytest
from typing import Dict, Any

class IntegrationTestSuite:
    """Comprehensive integration testing."""
    
    async def test_m365_integration(self):
        """Test Microsoft 365 integration."""
        auth_manager = GraphAuthManager(...)
        
        # Test authentication
        token = await auth_manager.get_access_token()
        assert token is not None
        
        # Test permissions
        permissions = await validate_m365_permissions()
        assert all(permissions.values()), f"Missing permissions: {permissions}"
        
        # Test email reading
        client = M365EmailClient(auth_manager)
        emails = await client.fetch_new_emails(limit=1)
        assert isinstance(emails, list)
    
    async def test_crm_integrations(self):
        """Test CRM system integrations."""
        gateway = CRMGateway(config_manager)
        await gateway.initialize()
        
        # Test each CRM
        for name, client in gateway.integrations.items():
            # Test authentication
            auth_result = await client.authenticate()
            assert auth_result, f"{name} authentication failed"
            
            # Test contact search
            contact = await client.search_contact("test@example.com")
            # Note: May return None if contact doesn't exist
    
    async def test_database_connections(self):
        """Test database connections."""
        connector = DatabaseConnector(database_config)
        await connector.initialize()
        
        # Test customer lookup
        customer = await connector.find_customer("test@example.com")
        # Note: May return None if customer doesn't exist
        
        # Test support history
        history = await connector.get_support_history("test@example.com")
        assert isinstance(history, list)

# Run tests
pytest.main([__file__, "-v"])
```

---

**Document Status**: Integration Ready  
**Last Updated**: January 2025  
**Next Review**: After successful integration testing 