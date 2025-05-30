# EmailBot - Implementation Guide

**Version**: 1.0  
**Last Updated**: January 2025  
**Purpose**: Detailed implementation patterns, templates, and code specifications

## 🎯 Implementation Overview

This guide provides detailed implementation patterns, code templates, and technical specifications for EmailBot development. It includes the specific prompts, configurations, and code structures outlined in the original architectural plan.

## 🤖 LLM Service Implementation

### Core Prompt Templates

#### Primary Classification Prompt
```python
CLASSIFICATION_PROMPT = """
You are an IT department email classifier for zgcompanies.com.

Email Details:
Sender: {sender_email}
Subject: {subject}
Body: {body}
Received: {timestamp}

Classify this email into EXACTLY ONE category:
1. PURCHASING - Purchase requests, vendor quotes, software licensing, hardware procurement
2. SUPPORT - Technical issues, system problems, user assistance, troubleshooting
3. INFORMATION - General inquiries, documentation requests, policy questions
4. ESCALATION - Urgent issues, executive requests, critical system failures
5. CONSULTATION - Strategic planning, architecture decisions, technology assessments

Provide your response in this exact JSON format:
{{
  "category": "CATEGORY_NAME",
  "confidence": 85,
  "reasoning": "Brief explanation of classification decision",
  "urgency": "LOW|MEDIUM|HIGH|CRITICAL",
  "suggested_action": "Specific recommended action",
  "required_expertise": ["list", "of", "required", "skills"],
  "estimated_effort": "minutes or hours estimate"
}}
"""

CONFIDENCE_ASSESSMENT_PROMPT = """
Analyze the following email classification and assess confidence:

Original Email:
Sender: {sender_email}
Subject: {subject}
Body: {body}

Classification Result:
Category: {category}
Reasoning: {reasoning}

Consider these factors for confidence scoring:
1. Clarity of intent in email content
2. Unambiguous categorization signals
3. Sufficient context for accurate classification
4. Absence of conflicting indicators

Provide confidence score (0-100) where:
- 90-100: Extremely clear, unambiguous classification
- 80-89: Clear classification with minor ambiguity
- 70-79: Generally clear but some uncertainty
- 60-69: Moderate confidence, multiple interpretations possible
- 50-59: Low confidence, significant ambiguity
- Below 50: Very uncertain, requires human review

Return only the confidence score as an integer.
"""

RESPONSE_GENERATION_PROMPT = """
Generate a professional, helpful response to this email:

Original Email:
From: {sender_email}
Subject: {subject}
Body: {body}

Classification: {category}
Urgency: {urgency}
Context: {context}

Response Guidelines:
1. Professional and courteous tone
2. Address the specific request or issue
3. Provide actionable next steps
4. Include relevant contact information
5. Set appropriate expectations for resolution time

Generate a response that would be appropriate for an IT department to send.
"""
```

#### Confidence Thresholds Configuration
```python
CONFIDENCE_THRESHOLDS = {
    "AUTO_HANDLE": 85,      # Process automatically with high confidence
    "SUGGEST_RESPONSE": 60,  # Provide suggested response for review
    "HUMAN_REVIEW": 40,     # Flag for manual review
    "ESCALATE_IMMEDIATE": 0  # Immediate escalation required
}

CATEGORY_CONFIDENCE_ADJUSTMENTS = {
    "PURCHASING": 0.95,     # High confidence threshold for purchases
    "SUPPORT": 0.85,        # Standard confidence for support
    "INFORMATION": 0.80,    # Lower threshold for info requests
    "ESCALATION": 0.90,     # High confidence for escalations
    "CONSULTATION": 0.75    # Lower threshold for consultations
}
```

### LLM Service Implementation Pattern

```python
import asyncio
import logging
from typing import Optional, Dict, Any
from openai import AsyncOpenAI
from app.models.email_models import EmailMessage, ClassificationResult
from app.utils.retry import AsyncRetry

logger = logging.getLogger(__name__)

class LLMService:
    """OpenAI GPT integration for email classification and response generation."""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.request_timeout = 30
        self.max_retries = 3
        
    @AsyncRetry(max_attempts=3, backoff_factor=2.0)
    async def classify_email(self, email: EmailMessage) -> ClassificationResult:
        """Classify email using structured LLM prompts."""
        try:
            prompt = CLASSIFICATION_PROMPT.format(
                sender_email=email.sender_email,
                subject=email.subject,
                body=email.body[:2000],  # Truncate for token limits
                timestamp=email.received_datetime.isoformat()
            )
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert IT email classifier."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent results
                max_tokens=300,
                timeout=self.request_timeout
            )
            
            # Parse JSON response
            result_text = response.choices[0].message.content.strip()
            classification_data = self._parse_classification_response(result_text)
            
            # Assess confidence
            confidence = await self._assess_confidence(email, classification_data)
            classification_data["confidence"] = confidence
            
            return ClassificationResult(**classification_data)
            
        except Exception as e:
            logger.error(f"Classification failed for email {email.id}: {str(e)}")
            raise LLMServiceError(f"Classification failed: {str(e)}")
    
    async def _assess_confidence(
        self, 
        email: EmailMessage, 
        classification: Dict[str, Any]
    ) -> float:
        """Assess confidence in classification result."""
        confidence_prompt = CONFIDENCE_ASSESSMENT_PROMPT.format(
            sender_email=email.sender_email,
            subject=email.subject,
            body=email.body[:1000],
            category=classification["category"],
            reasoning=classification["reasoning"]
        )
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You assess classification confidence."},
                    {"role": "user", "content": confidence_prompt}
                ],
                temperature=0.0,
                max_tokens=10
            )
            
            confidence_text = response.choices[0].message.content.strip()
            confidence = float(confidence_text)
            
            # Apply category-specific adjustments
            category = classification["category"]
            adjustment = CATEGORY_CONFIDENCE_ADJUSTMENTS.get(category, 1.0)
            
            return min(100.0, confidence * adjustment)
            
        except Exception as e:
            logger.warning(f"Confidence assessment failed: {str(e)}")
            return 50.0  # Default moderate confidence
    
    def _parse_classification_response(self, response_text: str) -> Dict[str, Any]:
        """Parse and validate LLM classification response."""
        import json
        
        try:
            # Extract JSON from response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            
            json_text = response_text[start_idx:end_idx]
            data = json.loads(json_text)
            
            # Validate required fields
            required_fields = ["category", "reasoning", "urgency", "suggested_action"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate category
            valid_categories = ["PURCHASING", "SUPPORT", "INFORMATION", "ESCALATION", "CONSULTATION"]
            if data["category"] not in valid_categories:
                raise ValueError(f"Invalid category: {data['category']}")
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to parse classification response: {str(e)}")
            raise LLMServiceError(f"Invalid response format: {str(e)}")

    async def generate_response_suggestion(
        self, 
        email: EmailMessage, 
        classification: ClassificationResult,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate suggested response for medium-confidence classifications."""
        context_str = self._format_context(context) if context else "No additional context"
        
        prompt = RESPONSE_GENERATION_PROMPT.format(
            sender_email=email.sender_email,
            subject=email.subject,
            body=email.body[:1500],
            category=classification.category,
            urgency=classification.urgency,
            context=context_str
        )
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You generate professional IT support responses."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Response generation failed: {str(e)}")
            return "Thank you for your email. We will review your request and respond shortly."
```

## 🎯 Email Processing Workflow

### Processing State Machine
```python
from enum import Enum
from typing import Dict, Callable, Any
import asyncio

class ProcessingState(Enum):
    """Email processing states."""
    RECEIVED = "received"
    VALIDATING = "validating"
    CLASSIFYING = "classifying"
    ROUTING = "routing"
    RESPONDING = "responding"
    ESCALATING = "escalating"
    COMPLETED = "completed"
    FAILED = "failed"

class EmailProcessor:
    """Central orchestrator for email processing workflow."""
    
    def __init__(
        self,
        llm_service: LLMService,
        m365_client: M365EmailClient,
        teams_manager: TeamsManager,
        confidence_router: ConfidenceRouter,
        database_service: DatabaseService
    ):
        self.llm_service = llm_service
        self.m365_client = m365_client
        self.teams_manager = teams_manager
        self.confidence_router = confidence_router
        self.database = database_service
        
        # State transition handlers
        self.state_handlers: Dict[ProcessingState, Callable] = {
            ProcessingState.RECEIVED: self._handle_received,
            ProcessingState.VALIDATING: self._handle_validation,
            ProcessingState.CLASSIFYING: self._handle_classification,
            ProcessingState.ROUTING: self._handle_routing,
            ProcessingState.RESPONDING: self._handle_responding,
            ProcessingState.ESCALATING: self._handle_escalating,
        }
    
    async def process_email(self, email: EmailMessage) -> ProcessingResult:
        """Process single email through complete workflow."""
        result = ProcessingResult(
            email_id=email.id,
            status=ProcessingState.RECEIVED.value,
            started_at=datetime.utcnow()
        )
        
        try:
            current_state = ProcessingState.RECEIVED
            
            while current_state not in [ProcessingState.COMPLETED, ProcessingState.FAILED]:
                logger.debug(f"Processing email {email.id} in state: {current_state.value}")
                
                # Execute state handler
                next_state, state_result = await self.state_handlers[current_state](
                    email, result
                )
                
                # Update result with state-specific data
                if state_result:
                    result.update(state_result)
                
                # Transition to next state
                current_state = next_state
                result.status = current_state.value
                
                # Save intermediate state
                await self.database.update_processing_result(result)
            
            result.completed_at = datetime.utcnow()
            result.processing_time_ms = (
                result.completed_at - result.started_at
            ).total_seconds() * 1000
            
            return result
            
        except Exception as e:
            logger.error(f"Email processing failed for {email.id}: {str(e)}")
            result.status = ProcessingState.FAILED.value
            result.error_message = str(e)
            result.completed_at = datetime.utcnow()
            
            await self.database.update_processing_result(result)
            return result
    
    async def _handle_classification(
        self, 
        email: EmailMessage, 
        result: ProcessingResult
    ) -> Tuple[ProcessingState, Dict[str, Any]]:
        """Handle email classification state."""
        try:
            classification = await self.llm_service.classify_email(email)
            
            return ProcessingState.ROUTING, {
                "classification": classification,
                "classification_completed_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Classification failed for {email.id}: {str(e)}")
            return ProcessingState.FAILED, {"error_message": str(e)}
    
    async def _handle_routing(
        self, 
        email: EmailMessage, 
        result: ProcessingResult
    ) -> Tuple[ProcessingState, Dict[str, Any]]:
        """Handle routing based on confidence."""
        classification = result.classification
        routing_action = await self.confidence_router.determine_action(
            email, classification
        )
        
        if routing_action == RoutingAction.AUTO_RESPOND:
            return ProcessingState.RESPONDING, {"routing_action": routing_action}
        elif routing_action == RoutingAction.ESCALATE:
            return ProcessingState.ESCALATING, {"routing_action": routing_action}
        else:
            # SUGGEST_RESPONSE or HUMAN_REVIEW
            return ProcessingState.COMPLETED, {
                "routing_action": routing_action,
                "requires_human_attention": True
            }
```

## 🚀 Teams Integration Implementation

### Team Assembly Logic
```python
class TeamsManager:
    """Microsoft Teams integration for escalation management."""
    
    # Expertise mapping for team assembly
    EXPERTISE_MAPPING = {
        "PURCHASING": ["finance", "procurement", "it_admin"],
        "SUPPORT": ["helpdesk", "system_admin", "network_admin"],
        "INFORMATION": ["it_admin", "documentation"],
        "ESCALATION": ["it_manager", "cio", "security"],
        "CONSULTATION": ["solution_architect", "it_manager", "vendor_relations"]
    }
    
    # User expertise database
    USER_EXPERTISE = {
        "admin@zgcompanies.com": ["it_admin", "system_admin"],
        "helpdesk@zgcompanies.com": ["helpdesk", "support"],
        "manager@zgcompanies.com": ["it_manager", "escalation"],
        "cio@zgcompanies.com": ["cio", "escalation", "consultation"],
        "finance@zgcompanies.com": ["finance", "procurement"],
        "security@zgcompanies.com": ["security", "escalation"]
    }
    
    async def create_escalation_group(
        self, 
        email: EmailMessage, 
        classification: ClassificationResult
    ) -> EscalationTeam:
        """Create Teams group for email escalation."""
        try:
            # Generate group name
            group_name = self._generate_group_name(email, classification)
            
            # Determine team members
            team_members = self._select_team_members(classification)
            
            # Create Teams chat group
            team_id = await self._create_teams_chat(group_name, team_members)
            
            # Post escalation message
            await self._post_escalation_message(team_id, email, classification)
            
            # Create escalation record
            escalation = EscalationTeam(
                team_id=team_id,
                email_id=email.id,
                team_name=group_name,
                members=team_members,
                created_at=datetime.utcnow()
            )
            
            return escalation
            
        except Exception as e:
            logger.error(f"Failed to create escalation group: {str(e)}")
            raise TeamsIntegrationError(f"Escalation creation failed: {str(e)}")
    
    def _generate_group_name(
        self, 
        email: EmailMessage, 
        classification: ClassificationResult
    ) -> str:
        """Generate descriptive Teams group name."""
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        subject_hash = hashlib.md5(email.subject.encode()).hexdigest()[:8]
        
        return f"IT-{classification.category}-{date_str}-{subject_hash}"
    
    def _select_team_members(self, classification: ClassificationResult) -> List[str]:
        """Select appropriate team members based on classification."""
        required_expertise = self.EXPERTISE_MAPPING.get(
            classification.category, 
            ["it_admin"]
        )
        
        # Add expertise from classification
        if classification.required_expertise:
            required_expertise.extend(classification.required_expertise)
        
        # Find users with required expertise
        selected_members = set()
        for user_email, user_skills in self.USER_EXPERTISE.items():
            if any(skill in required_expertise for skill in user_skills):
                selected_members.add(user_email)
        
        # Ensure minimum team size
        if len(selected_members) < 2:
            selected_members.add("admin@zgcompanies.com")  # Fallback admin
        
        return list(selected_members)
    
    async def _post_escalation_message(
        self, 
        team_id: str, 
        email: EmailMessage, 
        classification: ClassificationResult
    ):
        """Post structured escalation message to Teams group."""
        message = ESCALATION_MESSAGE_TEMPLATE.format(
            urgency=classification.urgency,
            sender=email.sender_email,
            subject=email.subject,
            timestamp=email.received_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            category=classification.category,
            confidence=classification.confidence,
            reasoning=classification.reasoning,
            effort=classification.estimated_effort,
            suggested_actions=classification.suggested_action,
            required_expertise=", ".join(classification.required_expertise or [])
        )
        
        await self.graph_client.post_team_message(team_id, message)
        
        # Attach original email if possible
        try:
            await self.graph_client.attach_email_to_chat(team_id, email.id)
        except Exception as e:
            logger.warning(f"Failed to attach email to chat: {str(e)}")

# Escalation message template
ESCALATION_MESSAGE_TEMPLATE = """
🚨 **EMAIL ESCALATION - {urgency}**

**Original Email:**
- From: {sender}
- Subject: {subject}
- Received: {timestamp}

**AI Analysis:**
- Category: {category} (Confidence: {confidence}%)
- Reasoning: {reasoning}
- Estimated Effort: {effort}

**Recommended Actions:**
{suggested_actions}

**Required Expertise:**
{required_expertise}

**Original Email:** [Attached]

React with ✅ when resolved or 🔄 if needs reassignment.
"""
```

## ⚙️ Configuration Management

### Integration Configuration Schema
```python
# integrations.json structure
INTEGRATION_CONFIG_SCHEMA = {
    "crm_systems": [
        {
            "name": "salesforce",
            "enabled": True,
            "priority": 1,
            "authentication": {
                "type": "oauth2",
                "client_id": "${SALESFORCE_CLIENT_ID}",
                "client_secret": "${SALESFORCE_CLIENT_SECRET}",
                "token_url": "https://login.salesforce.com/services/oauth2/token"
            },
            "api_config": {
                "base_url": "https://yourinstance.salesforce.com",
                "version": "v58.0",
                "timeout": 30,
                "retry_attempts": 3
            },
            "operations": {
                "search_contact": {
                    "endpoint": "/services/data/v{version}/search/",
                    "method": "GET",
                    "query_template": "FIND '{email}' IN EMAIL FIELDS RETURNING Contact(Id, Name, Email)"
                },
                "create_case": {
                    "endpoint": "/services/data/v{version}/sobjects/Case/",
                    "method": "POST",
                    "required_fields": ["Subject", "Description", "Origin"]
                }
            }
        }
    ],
    "databases": [
        {
            "name": "customer_db",
            "enabled": True,
            "type": "postgresql",
            "connection": {
                "host": "${DB_HOST}",
                "port": 5432,
                "database": "${DB_NAME}",
                "username": "${DB_USER}",
                "password": "${DB_PASSWORD}"
            },
            "queries": {
                "find_customer": "SELECT * FROM customers WHERE email = $1",
                "get_support_history": "SELECT * FROM support_tickets WHERE customer_email = $1 ORDER BY created_at DESC LIMIT 10"
            }
        }
    ],
    "webhook_endpoints": [
        {
            "name": "real_time_processing",
            "enabled": False,
            "url": "/webhooks/email",
            "authentication": {
                "type": "bearer_token",
                "token": "${WEBHOOK_TOKEN}"
            },
            "filters": {
                "sender_domains": ["zgcompanies.com"],
                "subjects_containing": ["urgent", "critical"]
            }
        }
    ]
}
```

### Configuration Manager Implementation
```python
class ConfigurationManager:
    """Dynamic configuration management with validation."""
    
    def __init__(self, config_file: str = "app/config/integrations.json"):
        self.config_file = config_file
        self.config_cache = {}
        self.last_reload = None
        self.reload_interval = 300  # 5 minutes
    
    async def load_integration_config(self, integration_type: str) -> Dict[str, Any]:
        """Load and validate integration configuration."""
        await self._ensure_config_loaded()
        
        configs = self.config_cache.get(integration_type, [])
        
        # Filter enabled configurations
        enabled_configs = [cfg for cfg in configs if cfg.get("enabled", False)]
        
        # Sort by priority
        enabled_configs.sort(key=lambda x: x.get("priority", 999))
        
        return enabled_configs
    
    async def validate_integration_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate integration configuration."""
        errors = []
        warnings = []
        
        try:
            # Test authentication
            auth_result = await self._test_authentication(config)
            if not auth_result.success:
                errors.append(f"Authentication failed: {auth_result.error}")
            
            # Test API endpoints
            api_result = await self._test_api_endpoints(config)
            if not api_result.success:
                warnings.append(f"API test failed: {api_result.error}")
            
            # Validate required fields
            required_fields = config.get("required_fields", [])
            for field in required_fields:
                if not config.get(field):
                    errors.append(f"Missing required field: {field}")
            
            return ValidationResult(
                success=len(errors) == 0,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            return ValidationResult(
                success=False,
                errors=[f"Validation error: {str(e)}"],
                warnings=[]
            )
```

## 🛡️ Security Implementation

### Data Sanitization and Encryption
```python
class SecurityManager:
    """Handle security, sanitization, and encryption."""
    
    def __init__(self, encryption_key: str):
        self.encryption_key = encryption_key.encode()
        self.cipher_suite = Fernet(base64.urlsafe_b64encode(self.encryption_key[:32]))
        
        # PII patterns for sanitization
        self.pii_patterns = [
            (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),  # SSN
            (r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', '[CARD]'),  # Credit card
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),  # Email (optional)
            (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP]'),  # IP address
        ]
    
    async def sanitize_email_content(self, content: str) -> Tuple[str, List[str]]:
        """Sanitize email content and return sanitized version + detected PII."""
        sanitized = content
        detected_pii = []
        
        for pattern, replacement in self.pii_patterns:
            matches = re.findall(pattern, content)
            if matches:
                detected_pii.extend([f"{replacement}: {len(matches)} instances"])
                sanitized = re.sub(pattern, replacement, sanitized)
        
        # Limit content length
        if len(sanitized) > 5000:
            sanitized = sanitized[:5000] + "[TRUNCATED]"
            detected_pii.append("Content truncated for processing")
        
        return sanitized, detected_pii
    
    async def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data for storage."""
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    async def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
    
    async def audit_log(
        self, 
        operation: str, 
        user: str, 
        resource: str, 
        details: Dict[str, Any] = None
    ):
        """Log security-relevant operations."""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": operation,
            "user": user,
            "resource": resource,
            "details": details or {},
            "ip_address": self._get_client_ip(),
            "user_agent": self._get_user_agent()
        }
        
        # Log to secure audit trail
        logger.info("AUDIT", extra=audit_entry)
        
        # Store in database
        await self._store_audit_entry(audit_entry)
```

## 📊 Monitoring and Metrics

### Performance Metrics Collection
```python
class MetricsCollector:
    """Collect and expose system metrics."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.metrics_prefix = "emailbot:metrics"
    
    async def record_email_processing(
        self, 
        email_id: str, 
        category: str, 
        confidence: float, 
        processing_time_ms: int,
        status: str
    ):
        """Record email processing metrics."""
        timestamp = int(time.time())
        
        # Time series metrics
        await self.redis.zadd(
            f"{self.metrics_prefix}:processing_times",
            {f"{timestamp}:{email_id}": processing_time_ms}
        )
        
        # Category distribution
        await self.redis.hincrby(
            f"{self.metrics_prefix}:categories",
            category,
            1
        )
        
        # Confidence distribution
        confidence_bucket = self._get_confidence_bucket(confidence)
        await self.redis.hincrby(
            f"{self.metrics_prefix}:confidence_distribution",
            confidence_bucket,
            1
        )
        
        # Status tracking
        await self.redis.hincrby(
            f"{self.metrics_prefix}:status_counts",
            status,
            1
        )
    
    async def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance metrics summary."""
        cutoff_time = int(time.time()) - (hours * 3600)
        
        # Get recent processing times
        processing_times = await self.redis.zrangebyscore(
            f"{self.metrics_prefix}:processing_times",
            cutoff_time,
            "+inf",
            withscores=True
        )
        
        times = [score for _, score in processing_times]
        
        return {
            "total_processed": len(times),
            "avg_processing_time": sum(times) / len(times) if times else 0,
            "min_processing_time": min(times) if times else 0,
            "max_processing_time": max(times) if times else 0,
            "category_distribution": await self.redis.hgetall(
                f"{self.metrics_prefix}:categories"
            ),
            "confidence_distribution": await self.redis.hgetall(
                f"{self.metrics_prefix}:confidence_distribution"
            ),
            "status_counts": await self.redis.hgetall(
                f"{self.metrics_prefix}:status_counts"
            )
        }
```

## 🔄 Retry and Error Handling Patterns

### Async Retry Decorator
```python
import asyncio
import logging
from typing import Callable, Type, Union
from functools import wraps

class AsyncRetry:
    """Async retry decorator with exponential backoff."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        backoff_factor: float = 2.0,
        exceptions: Union[Type[Exception], tuple] = Exception,
        on_retry: Callable = None
    ):
        self.max_attempts = max_attempts
        self.backoff_factor = backoff_factor
        self.exceptions = exceptions
        self.on_retry = on_retry or self._default_on_retry
    
    def __call__(self, func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, self.max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except self.exceptions as e:
                    last_exception = e
                    
                    if attempt == self.max_attempts:
                        break
                    
                    # Calculate backoff delay
                    delay = self.backoff_factor ** (attempt - 1)
                    
                    # Call retry callback
                    await self.on_retry(attempt, e, delay)
                    
                    # Wait before retry
                    await asyncio.sleep(delay)
            
            # All attempts failed
            raise last_exception
        
        return wrapper
    
    async def _default_on_retry(self, attempt: int, exception: Exception, delay: float):
        """Default retry callback."""
        logging.warning(
            f"Retry attempt {attempt} after {delay}s due to: {str(exception)}"
        )

# Circuit breaker pattern
class CircuitBreaker:
    """Circuit breaker for external service calls."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: int = 60,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def __call__(self, func: Callable):
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerError("Circuit breaker is OPEN")
        
        try:
            result = await func()
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        
        return (time.time() - self.last_failure_time) >= self.reset_timeout
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
```

## 🗄️ Database Patterns

### Repository Pattern Implementation
```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

class BaseRepository(ABC):
    """Base repository pattern for database operations."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    @abstractmethod
    async def create(self, entity: Any) -> Any:
        """Create new entity."""
        pass
    
    @abstractmethod
    async def get_by_id(self, entity_id: str) -> Optional[Any]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    async def update(self, entity: Any) -> Any:
        """Update existing entity."""
        pass
    
    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """Delete entity by ID."""
        pass

class EmailRepository(BaseRepository):
    """Repository for email operations."""
    
    async def create(self, email: EmailModel) -> EmailModel:
        """Create new email record."""
        self.db.add(email)
        await self.db.commit()
        await self.db.refresh(email)
        return email
    
    async def get_by_id(self, email_id: str) -> Optional[EmailModel]:
        """Get email by ID."""
        result = await self.db.execute(
            select(EmailModel).where(EmailModel.id == email_id)
        )
        return result.scalar_one_or_none()
    
    async def get_unprocessed_emails(self, limit: int = 50) -> List[EmailModel]:
        """Get emails that haven't been processed yet."""
        result = await self.db.execute(
            select(EmailModel)
            .where(EmailModel.processed_datetime.is_(None))
            .order_by(EmailModel.received_datetime.asc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def mark_as_processed(self, email_id: str, processing_result: ProcessingResult):
        """Mark email as processed with results."""
        await self.db.execute(
            update(EmailModel)
            .where(EmailModel.id == email_id)
            .values(
                processed_datetime=datetime.utcnow(),
                processing_status=processing_result.status
            )
        )
        await self.db.commit()
```

---

**Document Status**: Implementation Ready  
**Last Updated**: January 2025  
**Next Review**: After Phase 2 Sprint Completion 