import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from email.utils import parsedate_to_datetime

from msgraph import GraphServiceClient
from msgraph.generated.models.message import Message
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.recipient import Recipient
from msgraph.generated.models.email_address import EmailAddress

from app.models.email_models import EmailMessage
from app.utils.graph_auth import auth_manager
from app.config.settings import settings

logger = logging.getLogger(__name__)


class M365EmailClient:
    """Microsoft Graph API client for email operations."""
    
    def __init__(self):
        self.target_mailbox = settings.target_mailbox
        self.batch_size = settings.batch_size
        
    async def get_graph_client(self) -> GraphServiceClient:
        """Get authenticated Graph API client."""
        return await auth_manager.get_graph_client()
    
    async def fetch_new_emails(self, since_datetime: Optional[datetime] = None) -> List[EmailMessage]:
        """Fetch new emails from the target mailbox."""
        try:
            client = await self.get_graph_client()
            
            # Build OData filter for new emails
            filter_conditions = []
            
            if since_datetime:
                filter_datetime = since_datetime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                filter_conditions.append(f"receivedDateTime gt {filter_datetime}")
            
            # Only get unread emails
            filter_conditions.append("isRead eq false")
            
            # Combine filters
            filter_query = " and ".join(filter_conditions) if filter_conditions else None
            
            # Fetch messages
            request_config = {
                "$filter": filter_query,
                "$orderby": "receivedDateTime desc",
                "$top": self.batch_size,
                "$select": "id,subject,from,toRecipients,receivedDateTime,body,bodyPreview,hasAttachments,attachments,conversationId,importance,isRead"
            }
            
            messages_response = await client.users.by_user_id(self.target_mailbox).messages.get(
                request_configuration=request_config
            )
            
            emails = []
            if messages_response and messages_response.value:
                for message in messages_response.value:
                    email = await self._convert_message_to_email(message)
                    if email:
                        emails.append(email)
                        
            logger.info(f"Fetched {len(emails)} new emails from {self.target_mailbox}")
            return emails
            
        except Exception as e:
            logger.error(f"Error fetching emails: {str(e)}")
            raise
    
    async def _convert_message_to_email(self, message: Message) -> Optional[EmailMessage]:
        """Convert Graph API message to EmailMessage model."""
        try:
            # Extract sender information
            sender_email = None
            sender_name = None
            if message.from_ and message.from_.email_address:
                sender_email = message.from_.email_address.address
                sender_name = message.from_.email_address.name
            
            # Extract recipient information (first recipient)
            recipient_email = self.target_mailbox
            if message.to_recipients and len(message.to_recipients) > 0:
                first_recipient = message.to_recipients[0]
                if first_recipient.email_address:
                    recipient_email = first_recipient.email_address.address
            
            # Extract body content
            body_content = ""
            html_body = None
            if message.body:
                if message.body.content_type == BodyType.Text:
                    body_content = message.body.content or ""
                elif message.body.content_type == BodyType.Html:
                    html_body = message.body.content or ""
                    # Extract text from HTML for body field
                    body_content = self._extract_text_from_html(html_body)
            
            # Handle attachments
            attachments = []
            if message.has_attachments:
                # Note: Full attachment details would require additional API call
                attachments.append({"count": "has_attachments", "details": "requires_additional_fetch"})
            
            email = EmailMessage(
                id=message.id,
                sender_email=sender_email,
                sender_name=sender_name,
                recipient_email=recipient_email,
                subject=message.subject or "",
                body=body_content,
                html_body=html_body,
                received_datetime=message.received_date_time,
                attachments=attachments,
                conversation_id=message.conversation_id,
                importance=message.importance.name if message.importance else None
            )
            
            return email
            
        except Exception as e:
            logger.error(f"Error converting message to EmailMessage: {str(e)}")
            return None
    
    def _extract_text_from_html(self, html_content: str) -> str:
        """Extract plain text from HTML content."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup.get_text(separator=' ', strip=True)
        except ImportError:
            logger.warning("BeautifulSoup not available, returning raw HTML")
            return html_content
        except Exception as e:
            logger.error(f"Error extracting text from HTML: {str(e)}")
            return html_content
    
    async def send_reply(self, original_email: EmailMessage, reply_content: str, is_html: bool = False) -> bool:
        """Send a reply to an email."""
        try:
            client = await self.get_graph_client()
            
            # Create reply message body
            body = ItemBody(
                content_type=BodyType.Html if is_html else BodyType.Text,
                content=reply_content
            )
            
            # Create reply message
            reply_message = Message(
                subject=f"Re: {original_email.subject}",
                body=body,
                to_recipients=[
                    Recipient(
                        email_address=EmailAddress(
                            address=original_email.sender_email,
                            name=original_email.sender_name
                        )
                    )
                ]
            )
            
            # Send reply
            await client.users.by_user_id(self.target_mailbox).messages.post(reply_message)
            
            logger.info(f"Reply sent to {original_email.sender_email} for email {original_email.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending reply: {str(e)}")
            return False
    
    async def mark_as_read(self, email_id: str) -> bool:
        """Mark an email as read."""
        try:
            client = await self.get_graph_client()
            
            # Update message to mark as read
            update_message = Message(is_read=True)
            
            await client.users.by_user_id(self.target_mailbox).messages.by_message_id(email_id).patch(update_message)
            
            logger.debug(f"Marked email {email_id} as read")
            return True
            
        except Exception as e:
            logger.error(f"Error marking email as read: {str(e)}")
            return False
    
    async def get_email_details(self, email_id: str) -> Optional[EmailMessage]:
        """Get detailed information for a specific email."""
        try:
            client = await self.get_graph_client()
            
            message = await client.users.by_user_id(self.target_mailbox).messages.by_message_id(email_id).get()
            
            if message:
                return await self._convert_message_to_email(message)
            else:
                logger.warning(f"Email {email_id} not found")
                return None
                
        except Exception as e:
            logger.error(f"Error getting email details: {str(e)}")
            return None
    
    async def get_attachments(self, email_id: str) -> List[Dict[str, Any]]:
        """Get attachments for a specific email."""
        try:
            client = await self.get_graph_client()
            
            attachments_response = await client.users.by_user_id(self.target_mailbox).messages.by_message_id(email_id).attachments.get()
            
            attachments = []
            if attachments_response and attachments_response.value:
                for attachment in attachments_response.value:
                    attachment_info = {
                        "id": attachment.id,
                        "name": attachment.name,
                        "content_type": attachment.content_type,
                        "size": attachment.size
                    }
                    attachments.append(attachment_info)
            
            logger.debug(f"Retrieved {len(attachments)} attachments for email {email_id}")
            return attachments
            
        except Exception as e:
            logger.error(f"Error getting attachments: {str(e)}")
            return []
    
    async def create_folder(self, folder_name: str) -> Optional[str]:
        """Create a mail folder for organizing processed emails."""
        try:
            client = await self.get_graph_client()
            
            from msgraph.generated.models.mail_folder import MailFolder
            
            folder = MailFolder(display_name=folder_name)
            
            created_folder = await client.users.by_user_id(self.target_mailbox).mail_folders.post(folder)
            
            logger.info(f"Created mail folder: {folder_name}")
            return created_folder.id
            
        except Exception as e:
            logger.error(f"Error creating folder: {str(e)}")
            return None
    
    async def move_to_folder(self, email_id: str, folder_id: str) -> bool:
        """Move an email to a specific folder."""
        try:
            client = await self.get_graph_client()
            
            from msgraph.generated.models.move_post_request_body import MovePostRequestBody
            
            move_request = MovePostRequestBody(destination_id=folder_id)
            
            await client.users.by_user_id(self.target_mailbox).messages.by_message_id(email_id).move.post(move_request)
            
            logger.debug(f"Moved email {email_id} to folder {folder_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error moving email to folder: {str(e)}")
            return False
    
    async def test_connectivity(self) -> Dict[str, Any]:
        """Test connectivity to the target mailbox."""
        try:
            client = await self.get_graph_client()
            
            # Test basic mailbox access
            mailbox_info = await client.users.by_user_id(self.target_mailbox).get()
            
            # Test message access
            messages = await client.users.by_user_id(self.target_mailbox).messages.get(
                request_configuration={"$top": 1}
            )
            
            return {
                "status": "success",
                "mailbox_display_name": mailbox_info.display_name if mailbox_info else "Unknown",
                "mailbox_email": self.target_mailbox,
                "can_read_messages": messages is not None,
                "test_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Connectivity test failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "test_timestamp": datetime.utcnow().isoformat()
            }


# Global email client instance
email_client = M365EmailClient() 