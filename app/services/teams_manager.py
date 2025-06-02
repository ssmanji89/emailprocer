import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import uuid4

import httpx
from app.models.email_models import (
    EmailMessage, ClassificationResult, EscalationTeam,
    EmailCategory, UrgencyLevel
)
from app.core.auth_manager import auth_manager
from app.core.security import SecurityService
from app.config.settings import settings

logger = logging.getLogger(__name__)


class TeamsEscalationManager:
    """Microsoft Teams integration for email escalation management."""
    
    def __init__(self):
        self.security_service = SecurityService()
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.timeout = 30
        self.max_retries = 3
        
        # Predefined team member mappings based on expertise
        self.expertise_mappings = {
            "it_admin": [settings.default_it_admin_email],
            "helpdesk": [settings.default_helpdesk_email],
            "system_admin": [settings.default_system_admin_email],
            "network_admin": [settings.default_network_admin_email],
            "security": [settings.default_security_admin_email],
            "procurement": [settings.default_procurement_email],
            "it_manager": [settings.default_it_manager_email]
        }
        
        # Escalation statistics
        self.escalation_stats = {
            "total_escalations": 0,
            "teams_created": 0,
            "resolved_escalations": 0,
            "average_resolution_time_hours": 0
        }
    
    async def create_escalation_team(
        self, 
        email: EmailMessage, 
        classification: ClassificationResult,
        escalation_info: Dict[str, Any]
    ) -> EscalationTeam:
        """Create a Microsoft Teams group for email escalation."""
        try:
            logger.info(f"Creating escalation team for email {email.id}")
            
            # Generate team information
            team_name = self._generate_team_name(email, classification)
            team_members = self._determine_team_members(classification, escalation_info)
            
            # Create the Teams group
            team_creation_result = await self._create_teams_group(
                team_name=team_name,
                members=team_members,
                email=email,
                classification=classification
            )
            
            # Create escalation team record
            escalation_team = EscalationTeam(
                team_id=team_creation_result["team_id"],
                email_id=email.id,
                team_name=team_name,
                members=team_members,
                created_at=datetime.utcnow()
            )
            
            # Send initial escalation message
            await self._send_escalation_message(
                team_id=escalation_team.team_id,
                email=email,
                classification=classification,
                escalation_info=escalation_info
            )
            
            # Update statistics
            self.escalation_stats["total_escalations"] += 1
            self.escalation_stats["teams_created"] += 1
            
            logger.info(f"Escalation team {escalation_team.team_id} created successfully")
            return escalation_team
            
        except Exception as e:
            logger.error(f"Failed to create escalation team for email {email.id}: {str(e)}")
            raise
    
    def _generate_team_name(self, email: EmailMessage, classification: ClassificationResult) -> str:
        """Generate a descriptive team name for the escalation."""
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M")
        
        # Clean subject for team name
        clean_subject = email.subject[:30].replace(" ", "-").replace("/", "-")
        
        return f"EmailBot-{classification.category}-{timestamp}-{clean_subject}"
    
    def _determine_team_members(
        self, 
        classification: ClassificationResult, 
        escalation_info: Dict[str, Any]
    ) -> List[str]:
        """Determine appropriate team members based on classification and expertise needed."""
        members = set()
        
        # Add members based on required expertise
        required_expertise = escalation_info.get("team_members", classification.required_expertise)
        
        for expertise in required_expertise:
            if expertise in self.expertise_mappings:
                members.update(self.expertise_mappings[expertise])
        
        # Always include IT manager for high/critical urgency
        if classification.urgency in [UrgencyLevel.HIGH, UrgencyLevel.CRITICAL]:
            members.update(self.expertise_mappings.get("it_manager", []))
        
        # Category-specific additions
        if classification.category == EmailCategory.PURCHASING:
            members.update(self.expertise_mappings.get("procurement", []))
        elif classification.category == EmailCategory.ESCALATION:
            members.update(self.expertise_mappings.get("it_manager", []))
            members.update(self.expertise_mappings.get("security", []))
        
        # Ensure we have at least one member
        if not members:
            members.update(self.expertise_mappings.get("it_admin", []))
        
        return list(members)
    
    async def _create_teams_group(
        self, 
        team_name: str, 
        members: List[str],
        email: EmailMessage,
        classification: ClassificationResult
    ) -> Dict[str, Any]:
        """Create the actual Microsoft Teams group."""
        try:
            # Get authenticated client
            access_token = await auth_manager.get_access_token()
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Create group request
            group_data = {
                "displayName": team_name,
                "description": f"EmailBot escalation for email from {email.sender_email}: {email.subject}",
                "groupTypes": ["Unified"],
                "mailEnabled": True,
                "mailNickname": team_name.lower().replace("-", "").replace("_", "")[:50],
                "securityEnabled": False,
                "visibility": "Private"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Create the group
                response = await client.post(
                    f"{self.base_url}/groups",
                    headers=headers,
                    json=group_data
                )
                
                if response.status_code not in [200, 201]:
                    raise Exception(f"Failed to create group: {response.status_code} - {response.text}")
                
                group_info = response.json()
                group_id = group_info["id"]
                
                # Wait for group provisioning
                await asyncio.sleep(2)
                
                # Add members to the group
                await self._add_members_to_group(group_id, members, headers)
                
                # Enable Teams for the group
                teams_info = await self._enable_teams_for_group(group_id, headers)
                
                return {
                    "team_id": group_id,
                    "team_name": team_name,
                    "members_added": len(members),
                    "teams_enabled": teams_info.get("teams_enabled", False)
                }
                
        except Exception as e:
            logger.error(f"Error creating Teams group: {str(e)}")
            raise
    
    async def _add_members_to_group(
        self, 
        group_id: str, 
        members: List[str], 
        headers: Dict[str, str]
    ) -> None:
        """Add members to the Teams group."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                for member_email in members:
                    try:
                        # Get user ID from email
                        user_response = await client.get(
                            f"{self.base_url}/users/{member_email}",
                            headers=headers
                        )
                        
                        if user_response.status_code == 200:
                            user_info = user_response.json()
                            user_id = user_info["id"]
                            
                            # Add user to group
                            member_data = {
                                "@odata.id": f"https://graph.microsoft.com/v1.0/directoryObjects/{user_id}"
                            }
                            
                            await client.post(
                                f"{self.base_url}/groups/{group_id}/members/$ref",
                                headers=headers,
                                json=member_data
                            )
                            
                            logger.debug(f"Added {member_email} to group {group_id}")
                        else:
                            logger.warning(f"Could not find user {member_email}: {user_response.status_code}")
                            
                    except Exception as e:
                        logger.warning(f"Failed to add member {member_email}: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Error adding members to group: {str(e)}")
            raise
    
    async def _enable_teams_for_group(self, group_id: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """Enable Microsoft Teams functionality for the group."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Teams creation payload
                team_data = {
                    "template@odata.bind": "https://graph.microsoft.com/v1.0/teamsTemplates('standard')",
                    "group@odata.bind": f"https://graph.microsoft.com/v1.0/groups('{group_id}')"
                }
                
                response = await client.post(
                    f"{self.base_url}/teams",
                    headers=headers,
                    json=team_data
                )
                
                if response.status_code in [200, 201, 202]:
                    logger.info(f"Teams functionality enabled for group {group_id}")
                    return {"teams_enabled": True}
                else:
                    logger.warning(f"Failed to enable Teams: {response.status_code} - {response.text}")
                    return {"teams_enabled": False, "error": response.text}
                    
        except Exception as e:
            logger.error(f"Error enabling Teams for group: {str(e)}")
            return {"teams_enabled": False, "error": str(e)}
    
    async def _send_escalation_message(
        self,
        team_id: str,
        email: EmailMessage,
        classification: ClassificationResult,
        escalation_info: Dict[str, Any]
    ) -> None:
        """Send initial escalation message to the Teams group."""
        try:
            access_token = await auth_manager.get_access_token()
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Create escalation message
            message_body = self._build_escalation_message(email, classification, escalation_info)
            
            message_data = {
                "body": {
                    "contentType": "html",
                    "content": message_body
                }
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Wait for Teams to be fully provisioned
                await asyncio.sleep(5)
                
                # Send message to general channel
                response = await client.post(
                    f"{self.base_url}/teams/{team_id}/channels/general/messages",
                    headers=headers,
                    json=message_data
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"Escalation message sent to team {team_id}")
                else:
                    logger.warning(f"Failed to send escalation message: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error sending escalation message: {str(e)}")
    
    def _build_escalation_message(
        self,
        email: EmailMessage,
        classification: ClassificationResult,
        escalation_info: Dict[str, Any]
    ) -> str:
        """Build formatted escalation message for Teams."""
        return f"""
<h2>🚨 EmailBot Escalation</h2>

<h3>Email Details</h3>
<ul>
<li><strong>From:</strong> {email.sender_email}</li>
<li><strong>Subject:</strong> {email.subject}</li>
<li><strong>Received:</strong> {email.received_datetime.strftime('%Y-%m-%d %H:%M:%S UTC')}</li>
<li><strong>Email ID:</strong> {email.id}</li>
</ul>

<h3>Classification Results</h3>
<ul>
<li><strong>Category:</strong> {classification.category}</li>
<li><strong>Confidence:</strong> {classification.confidence}%</li>
<li><strong>Urgency:</strong> {classification.urgency}</li>
<li><strong>Estimated Effort:</strong> {classification.estimated_effort}</li>
</ul>

<h3>Reasoning</h3>
<p>{classification.reasoning}</p>

<h3>Suggested Action</h3>
<p>{classification.suggested_action}</p>

<h3>Escalation Details</h3>
<ul>
<li><strong>Reason:</strong> {escalation_info.get('escalation_reason', 'Standard escalation')}</li>
<li><strong>Priority:</strong> {escalation_info.get('priority', 'medium')}</li>
<li><strong>Estimated Resolution:</strong> {escalation_info.get('estimated_resolution_time', 'Unknown')}</li>
</ul>

<h3>Initial Actions</h3>
<ul>
{self._format_list_items(escalation_info.get('suggested_initial_actions', []))}
</ul>

<h3>Required Resources</h3>
<ul>
{self._format_list_items(escalation_info.get('resources_needed', []))}
</ul>

<h3>Email Content</h3>
<blockquote>
{email.body[:500]}{"..." if len(email.body) > 500 else ""}
</blockquote>

<hr>
<p><em>This escalation was automatically created by EmailBot. Please acknowledge and assign ownership.</em></p>
"""
    
    def _format_list_items(self, items: List[str]) -> str:
        """Format list items for HTML display."""
        if not items:
            return "<li>None specified</li>"
        return "".join([f"<li>{item}</li>" for item in items])
    
    async def resolve_escalation(self, team_id: str, resolution_notes: str) -> bool:
        """Mark an escalation as resolved."""
        try:
            # Send resolution message
            access_token = await auth_manager.get_access_token()
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            resolution_message = f"""
<h3>✅ Escalation Resolved</h3>
<p><strong>Resolution Notes:</strong></p>
<blockquote>{resolution_notes}</blockquote>
<p><em>Resolved at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</em></p>
"""
            
            message_data = {
                "body": {
                    "contentType": "html", 
                    "content": resolution_message
                }
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/teams/{team_id}/channels/general/messages",
                    headers=headers,
                    json=message_data
                )
                
                if response.status_code in [200, 201]:
                    self.escalation_stats["resolved_escalations"] += 1
                    logger.info(f"Escalation {team_id} marked as resolved")
                    return True
                else:
                    logger.error(f"Failed to send resolution message: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error resolving escalation {team_id}: {str(e)}")
            return False
    
    async def test_connectivity(self) -> Dict[str, Any]:
        """Test Teams integration connectivity."""
        try:
            access_token = await auth_manager.get_access_token()
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Test basic Graph API access
                response = await client.get(
                    f"{self.base_url}/me",
                    headers=headers
                )
                
                if response.status_code == 200:
                    user_info = response.json()
                    return {
                        "status": "success",
                        "user_principal": user_info.get("userPrincipalName"),
                        "display_name": user_info.get("displayName"),
                        "test_timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    return {
                        "status": "error",
                        "error": f"API test failed: {response.status_code}",
                        "test_timestamp": datetime.utcnow().isoformat()
                    }
                    
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "test_timestamp": datetime.utcnow().isoformat()
            }
    
    def get_escalation_statistics(self) -> Dict[str, Any]:
        """Get escalation statistics."""
        return {
            **self.escalation_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def list_active_escalations(self) -> List[Dict[str, Any]]:
        """List currently active escalation teams."""
        try:
            access_token = await auth_manager.get_access_token()
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Get groups created by EmailBot (filter by naming convention)
                response = await client.get(
                    f"{self.base_url}/groups",
                    headers=headers,
                    params={"$filter": "startswith(displayName,'EmailBot-')"}
                )
                
                if response.status_code == 200:
                    groups = response.json().get("value", [])
                    return [
                        {
                            "team_id": group["id"],
                            "team_name": group["displayName"],
                            "created_date": group["createdDateTime"],
                            "description": group.get("description", "")
                        }
                        for group in groups
                    ]
                else:
                    logger.error(f"Failed to list escalations: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error listing active escalations: {str(e)}")
            return []


# Singleton instance for use across the application  
teams_manager = TeamsEscalationManager() 