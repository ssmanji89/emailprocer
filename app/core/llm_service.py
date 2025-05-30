import asyncio
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from openai import AsyncOpenAI

from app.models.email_models import EmailMessage, ClassificationResult, EmailCategory, UrgencyLevel
from app.config.settings import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM-powered email classification and analysis."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.max_tokens = settings.openai_max_tokens
        self.temperature = settings.openai_temperature
        self.max_retries = settings.max_retries
        self.retry_delay = settings.retry_delay_seconds
    
    async def classify_email(self, email: EmailMessage) -> ClassificationResult:
        """Classify email using LLM and return structured result."""
        try:
            classification_prompt = self._build_classification_prompt(email)
            
            response = await self._call_llm_with_retry(
                prompt=classification_prompt,
                system_message="You are an expert IT department email classifier for zgcompanies.com. Analyze emails and provide accurate categorization with confidence scores."
            )
            
            # Parse LLM response
            classification_data = self._parse_classification_response(response)
            
            # Create ClassificationResult object
            result = ClassificationResult(
                category=EmailCategory(classification_data.get("category", "INFORMATION")),
                confidence=float(classification_data.get("confidence", 50)),
                reasoning=classification_data.get("reasoning", "Unable to determine classification reasoning"),
                urgency=UrgencyLevel(classification_data.get("urgency", "MEDIUM")),
                suggested_action=classification_data.get("suggested_action", "Manual review required"),
                required_expertise=classification_data.get("required_expertise", []),
                estimated_effort=classification_data.get("estimated_effort", "Unknown")
            )
            
            logger.info(f"Email {email.id} classified as {result.category} with {result.confidence}% confidence")
            return result
            
        except Exception as e:
            logger.error(f"Error classifying email {email.id}: {str(e)}")
            # Return fallback classification
            return ClassificationResult(
                category=EmailCategory.INFORMATION,
                confidence=0.0,
                reasoning=f"Classification failed: {str(e)}",
                urgency=UrgencyLevel.MEDIUM,
                suggested_action="Manual review required due to classification error",
                required_expertise=["it_admin"],
                estimated_effort="Unknown"
            )
    
    def _build_classification_prompt(self, email: EmailMessage) -> str:
        """Build the classification prompt for the LLM."""
        return f"""
You are an IT department email classifier for zgcompanies.com.

Email Details:
Sender: {email.sender_email}
Sender Name: {email.sender_name or 'N/A'}
Subject: {email.subject}
Received: {email.received_datetime.isoformat()}
Body: {email.body[:2000]}  # Limit body to 2000 chars

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

Consider these factors:
- Sender domain and email patterns
- Subject line keywords and urgency indicators
- Body content and technical terminology
- Business context and organizational needs
"""
    
    async def generate_response_suggestion(self, email: EmailMessage, classification: ClassificationResult) -> str:
        """Generate a suggested response for the email."""
        try:
            response_prompt = self._build_response_prompt(email, classification)
            
            response = await self._call_llm_with_retry(
                prompt=response_prompt,
                system_message="You are a helpful IT support assistant. Generate professional, accurate, and helpful email responses."
            )
            
            logger.info(f"Generated response suggestion for email {email.id}")
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error generating response for email {email.id}: {str(e)}")
            return f"Thank you for your email. We have received your {classification.category.lower()} request and will respond as soon as possible."
    
    def _build_response_prompt(self, email: EmailMessage, classification: ClassificationResult) -> str:
        """Build the response generation prompt."""
        return f"""
Generate a professional email response for this IT department inquiry:

Original Email:
From: {email.sender_email}
Subject: {email.subject}
Body: {email.body[:1500]}

Classification: {classification.category}
Urgency: {classification.urgency}
Confidence: {classification.confidence}%

Guidelines:
- Be professional and helpful
- Acknowledge the specific request
- Provide relevant information or next steps
- Include appropriate timeframes
- Use zgcompanies.com email signature style
- Keep response concise but complete

Generate a response that addresses their specific needs:
"""
    
    async def assess_escalation_needs(self, email: EmailMessage, classification: ClassificationResult) -> Dict[str, Any]:
        """Assess what type of escalation is needed and who should be involved."""
        try:
            escalation_prompt = self._build_escalation_prompt(email, classification)
            
            response = await self._call_llm_with_retry(
                prompt=escalation_prompt,
                system_message="You are an IT escalation specialist. Determine appropriate team composition and escalation strategies."
            )
            
            escalation_data = self._parse_json_response(response)
            
            logger.info(f"Assessed escalation needs for email {email.id}")
            return escalation_data
            
        except Exception as e:
            logger.error(f"Error assessing escalation for email {email.id}: {str(e)}")
            return {
                "team_members": ["it_admin"],
                "escalation_reason": "Standard escalation due to assessment error",
                "priority": "medium",
                "estimated_resolution_time": "1-2 hours"
            }
    
    def _build_escalation_prompt(self, email: EmailMessage, classification: ClassificationResult) -> str:
        """Build the escalation assessment prompt."""
        return f"""
Assess escalation needs for this IT email:

Email: {email.subject}
From: {email.sender_email}
Category: {classification.category}
Urgency: {classification.urgency}
Confidence: {classification.confidence}%
Required Expertise: {', '.join(classification.required_expertise)}

Determine escalation strategy in JSON format:
{{
  "team_members": ["list of required team member roles"],
  "escalation_reason": "clear explanation of why escalation is needed",
  "priority": "low|medium|high|critical",
  "estimated_resolution_time": "time estimate",
  "suggested_initial_actions": ["list of immediate actions to take"],
  "resources_needed": ["list of systems, documentation, or tools needed"]
}}

Available team roles:
- it_admin (general IT administration)
- helpdesk (user support)
- system_admin (server and infrastructure)
- network_admin (networking and connectivity)
- security (cybersecurity and compliance)
- procurement (purchasing and vendor relations)
- it_manager (management and decision making)
"""
    
    async def _call_llm_with_retry(self, prompt: str, system_message: str) -> str:
        """Call LLM with retry logic and error handling."""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ]
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    timeout=settings.request_timeout_seconds
                )
                
                if response.choices and len(response.choices) > 0:
                    return response.choices[0].message.content
                else:
                    raise Exception("No response content received from LLM")
                    
            except Exception as e:
                last_exception = e
                logger.warning(f"LLM call attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
        
        raise Exception(f"LLM call failed after {self.max_retries} attempts: {str(last_exception)}")
    
    def _parse_classification_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate LLM classification response."""
        try:
            # Extract JSON from response if it contains additional text
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_text = response[json_start:json_end].strip()
            elif "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_text = response[json_start:json_end]
            else:
                json_text = response
            
            data = json.loads(json_text)
            
            # Validate required fields
            if "category" not in data:
                data["category"] = "INFORMATION"
            if "confidence" not in data:
                data["confidence"] = 50
            if "reasoning" not in data:
                data["reasoning"] = "No reasoning provided"
            if "urgency" not in data:
                data["urgency"] = "MEDIUM"
            if "suggested_action" not in data:
                data["suggested_action"] = "Manual review required"
            if "required_expertise" not in data:
                data["required_expertise"] = ["it_admin"]
            if "estimated_effort" not in data:
                data["estimated_effort"] = "Unknown"
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            logger.error(f"Raw response: {response}")
            
            # Return fallback data
            return {
                "category": "INFORMATION",
                "confidence": 25,
                "reasoning": "Failed to parse LLM response",
                "urgency": "MEDIUM",
                "suggested_action": "Manual review required",
                "required_expertise": ["it_admin"],
                "estimated_effort": "Unknown"
            }
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from LLM with error handling."""
        try:
            # Extract JSON from response
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_text = response[json_start:json_end].strip()
            elif "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_text = response[json_start:json_end]
            else:
                json_text = response
            
            return json.loads(json_text)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            return {}
    
    async def analyze_email_patterns(self, emails: list[EmailMessage]) -> Dict[str, Any]:
        """Analyze a batch of emails to identify patterns."""
        try:
            if not emails:
                return {"patterns": [], "insights": "No emails provided for analysis"}
            
            pattern_prompt = self._build_pattern_analysis_prompt(emails)
            
            response = await self._call_llm_with_retry(
                prompt=pattern_prompt,
                system_message="You are a data analyst specializing in email pattern recognition. Identify recurring themes and automation opportunities."
            )
            
            pattern_data = self._parse_json_response(response)
            
            logger.info(f"Analyzed patterns for {len(emails)} emails")
            return pattern_data
            
        except Exception as e:
            logger.error(f"Error analyzing email patterns: {str(e)}")
            return {"patterns": [], "insights": f"Pattern analysis failed: {str(e)}"}
    
    def _build_pattern_analysis_prompt(self, emails: list[EmailMessage]) -> str:
        """Build prompt for pattern analysis."""
        email_summaries = []
        for email in emails[:20]:  # Limit to first 20 emails
            summary = {
                "sender": email.sender_email,
                "subject": email.subject,
                "category": "unknown",  # Will be filled by classification
                "body_preview": email.body[:200]
            }
            email_summaries.append(summary)
        
        return f"""
Analyze these email patterns and identify automation opportunities:

Emails to analyze:
{json.dumps(email_summaries, indent=2)}

Provide analysis in JSON format:
{{
  "patterns": [
    {{
      "pattern_type": "subject_line|sender_domain|content_theme",
      "description": "clear description of the pattern",
      "frequency": "how often this occurs",
      "automation_potential": "0-100 score",
      "suggested_automation": "what could be automated"
    }}
  ],
  "insights": "overall insights about email patterns",
  "recommendations": ["list of specific recommendations for automation"]
}}

Focus on:
- Recurring subject line patterns
- Common sender types (vendors, users, systems)
- Repetitive request types
- Time-based patterns
- Automation opportunities
"""


# Global LLM service instance
llm_service = LLMService() 