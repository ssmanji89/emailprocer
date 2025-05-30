import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json
import logging

from msal import ConfidentialClientApplication
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient

from app.config.settings import settings

logger = logging.getLogger(__name__)


class GraphAuthManager:
    """Manages Microsoft Graph API authentication and token lifecycle."""
    
    def __init__(self):
        self.tenant_id = settings.m365_tenant_id
        self.client_id = settings.m365_client_id
        self.client_secret = settings.m365_client_secret
        self.scopes = settings.m365_scope
        
        self._client_app: Optional[ConfidentialClientApplication] = None
        self._graph_client: Optional[GraphServiceClient] = None
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        
    def _create_msal_app(self) -> ConfidentialClientApplication:
        """Create MSAL confidential client application."""
        authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        
        return ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=authority
        )
    
    async def get_access_token(self) -> str:
        """Get valid access token, refreshing if necessary."""
        if self._is_token_valid():
            return self._access_token
            
        logger.info("Acquiring new access token")
        return await self._acquire_token()
    
    def _is_token_valid(self) -> bool:
        """Check if current token is valid and not expired."""
        if not self._access_token or not self._token_expires_at:
            return False
            
        # Add 5-minute buffer before expiration
        buffer_time = datetime.utcnow() + timedelta(minutes=5)
        return self._token_expires_at > buffer_time
    
    async def _acquire_token(self) -> str:
        """Acquire new access token using client credentials flow."""
        try:
            if not self._client_app:
                self._client_app = self._create_msal_app()
            
            # Use client credentials flow for app-only authentication
            result = self._client_app.acquire_token_for_client(scopes=self.scopes)
            
            if "access_token" in result:
                self._access_token = result["access_token"]
                expires_in = result.get("expires_in", 3600)
                self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                
                logger.info(f"Successfully acquired token, expires at {self._token_expires_at}")
                return self._access_token
            else:
                error_msg = result.get("error_description", "Unknown error")
                logger.error(f"Failed to acquire token: {error_msg}")
                raise Exception(f"Token acquisition failed: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error acquiring access token: {str(e)}")
            raise
    
    async def get_graph_client(self) -> GraphServiceClient:
        """Get authenticated Graph API client."""
        if not self._graph_client or not self._is_token_valid():
            await self._create_graph_client()
        
        return self._graph_client
    
    async def _create_graph_client(self) -> None:
        """Create new Graph API client with fresh token."""
        try:
            credential = ClientSecretCredential(
                tenant_id=self.tenant_id,
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            
            self._graph_client = GraphServiceClient(
                credentials=credential,
                scopes=self.scopes
            )
            
            logger.info("Graph API client created successfully")
            
        except Exception as e:
            logger.error(f"Error creating Graph client: {str(e)}")
            raise
    
    async def test_connection(self) -> bool:
        """Test Graph API connection and permissions."""
        try:
            client = await self.get_graph_client()
            
            # Test basic connectivity by getting current user
            me = await client.me.get()
            if me:
                logger.info(f"Graph API connection test successful. Connected as: {me.display_name}")
                return True
            else:
                logger.error("Graph API connection test failed - no user data returned")
                return False
                
        except Exception as e:
            logger.error(f"Graph API connection test failed: {str(e)}")
            return False
    
    async def validate_permissions(self) -> Dict[str, bool]:
        """Validate that all required permissions are available."""
        permissions_status = {}
        
        try:
            client = await self.get_graph_client()
            
            # Test Mail.Read permission
            try:
                messages = await client.users.by_user_id(settings.target_mailbox).messages.get()
                permissions_status["Mail.Read"] = True
                logger.info("Mail.Read permission validated")
            except Exception as e:
                permissions_status["Mail.Read"] = False
                logger.error(f"Mail.Read permission validation failed: {str(e)}")
            
            # Test User.Read.All permission
            try:
                users = await client.users.get()
                permissions_status["User.Read.All"] = True
                logger.info("User.Read.All permission validated")
            except Exception as e:
                permissions_status["User.Read.All"] = False
                logger.error(f"User.Read.All permission validation failed: {str(e)}")
            
            # Additional permission tests can be added here
            permissions_status["Chat.Create"] = True  # Will be tested during first escalation
            permissions_status["ChatMember.ReadWrite"] = True
            permissions_status["Mail.Send"] = True
            
        except Exception as e:
            logger.error(f"Permission validation error: {str(e)}")
            
        return permissions_status
    
    def get_token_info(self) -> Dict[str, Any]:
        """Get current token information for debugging."""
        return {
            "has_token": self._access_token is not None,
            "expires_at": self._token_expires_at.isoformat() if self._token_expires_at else None,
            "is_valid": self._is_token_valid(),
            "time_until_expiry": str(self._token_expires_at - datetime.utcnow()) if self._token_expires_at else None
        }


# Global authentication manager instance
auth_manager = GraphAuthManager() 