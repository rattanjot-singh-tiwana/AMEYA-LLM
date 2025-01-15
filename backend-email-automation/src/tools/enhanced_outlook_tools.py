# src/tools/enhanced_outlook_tools.py
from .OutlookTools import OutlookTools
from datetime import datetime, timedelta
import os

class EnhancedOutlookTools(OutlookTools):
    def __init__(self, email_address):
        client_id = os.getenv('OUTLOOK_CLIENT_ID')
        client_secret = os.getenv('OUTLOOK_CLIENT_SECRET')
        tenant_id = os.getenv('OUTLOOK_TENANT_ID')
        super().__init__(client_id, client_secret, tenant_id)
        self.email_address = email_address

    async def fetch_unanswered_emails(self, max_results=50):
        """Fetch unanswered emails from Outlook"""
        try:
            # Fetch recent emails
            emails = self.fetch_emails(top=max_results)
            unanswered_emails = []

            # Get draft emails
            drafts = await self.fetch_draft_replies()
            threads_with_drafts = {draft.get('conversationId') for draft in drafts}

            for email in emails.get('value', []):
                if (email.get('conversationId') not in threads_with_drafts and 
                    not self._should_skip_email(email)):
                    email_info = self._get_email_info(email)
                    unanswered_emails.append(email_info)

            return unanswered_emails
        except Exception as e:
            print(f"Error fetching Outlook emails: {e}")
            return []

    async def create_draft_reply(self, initial_email, reply_text):
        """Create a draft reply in Outlook"""
        try:
            return self.draft_email(
                subject=f"Re: {initial_email.subject}",
                body=reply_text,
                to_emails=[initial_email.sender]
            )
        except Exception as e:
            print(f"Error creating Outlook draft: {e}")
            return None

    async def fetch_draft_replies(self):
        """Fetch draft emails from Outlook"""
        try:
            return self._make_request("GET", "/me/mailFolders/drafts/messages").get('value', [])
        except Exception as e:
            print(f"Error fetching Outlook drafts: {e}")
            return []

    def _get_email_info(self, email):
        """Convert Outlook email format to standard format"""
        return {
            "id": email.get("id"),
            "threadId": email.get("conversationId"),
            "messageId": email.get("internetMessageId"),
            "references": email.get("conversationId", ""),
            "sender": email.get("from", {}).get("emailAddress", {}).get("address", "Unknown"),
            "subject": email.get("subject", "No Subject"),
            "body": email.get("body", {}).get("content", ""),
            "isUnread": email.get("isRead", True),
            "labels": email.get("categories", [])
        }

    def _should_skip_email(self, email):
        """Check if email should be skipped"""
        sender = email.get("from", {}).get("emailAddress", {}).get("address", "")
        return self.email_address.lower() in sender.lower()
    
    async def send_reply(self, initial_email, reply_text):
        """Send a reply email using Outlook"""
        try:
            return self.send_email(
                from_email=self.email_address,
                to_emails=[initial_email.sender],
                subject=f"Re: {initial_email.subject}",
                body=reply_text
            )
        except Exception as e:
            print(f"Error sending Outlook reply: {e}")
            return None