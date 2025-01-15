import os
import re
import uuid
import base64
import asyncio
from functools import partial
from tenacity import retry, stop_after_attempt, wait_exponential
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

class GmailToolsClass:
    def __init__(self):
        self.service = self._get_gmail_service()
        if not self.check_credentials():
            raise Exception("Gmail authentication failed. Please check credentials.")
        
        self.retry_config = {
            'stop': stop_after_attempt(3),
            'wait': wait_exponential(multiplier=1, min=4, max=10)
        }

    def check_credentials(self):
        """Verify Gmail credentials and connection"""
        try:
            self.service.users().getProfile(userId='me').execute()
            return True
        except Exception as e:
            print(f"Gmail credentials error: {str(e)}")
            print("Please ensure:")
            print("1. credentials.json is in the root directory")
            print("2. token.json is valid (delete it to re-authenticate)")
            print("3. Your network connection is stable")
            print("4. The Gmail API is enabled in your Google Cloud Console")
            return False

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _safe_api_call(self, api_func):
        """Safely execute Gmail API calls with retry logic"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, api_func)
        except Exception as e:
            print(f"API call failed: {str(e)}")
            raise

    async def fetch_unanswered_emails(self, max_results=50):
        """Fetches all emails included in unanswered threads."""
        try:
            recent_emails = await self.fetch_recent_emails(max_results)
            if not recent_emails: 
                return []
            
            drafts = await self.fetch_draft_replies()
            threads_with_drafts = {draft['threadId'] for draft in drafts}

            seen_threads = set()
            unanswered_emails = []
            
            for email in recent_emails:
                thread_id = email['threadId']
                if thread_id not in seen_threads and thread_id not in threads_with_drafts:
                    seen_threads.add(thread_id)
                    email_info = await self._get_email_info(email['id'])
                    if await self._should_skip_email(email_info):
                        continue
                    unanswered_emails.append(email_info)
            
            return unanswered_emails

        except Exception as e:
            print(f"An error occurred in fetch_unanswered_emails: {e}")
            return []

    async def fetch_recent_emails(self, max_results=500):
        """Fetch recent emails with improved error handling."""
        try:
            now = datetime.now()
            delay = now - timedelta(hours=24)
            query = f'after:{int(delay.timestamp())}'
            
            list_messages = partial(
                self.service.users().messages().list(
                    userId="me",
                    q=query,
                    maxResults=max_results
                ).execute
            )
            results = await self._safe_api_call(list_messages)
            
            messages = results.get("messages", [])
            if not messages:
                return []

            chunk_size = 10
            detailed_messages = []
            
            for i in range(0, len(messages), chunk_size):
                chunk = messages[i:i + chunk_size]
                chunk_tasks = [
                    self._fetch_message_detail(message['id'])
                    for message in chunk
                ]
                
                try:
                    chunk_results = await asyncio.gather(
                        *chunk_tasks,
                        return_exceptions=True
                    )
                    detailed_messages.extend([
                        msg for msg in chunk_results 
                        if msg is not None and not isinstance(msg, Exception)
                    ])
                except Exception as e:
                    print(f"Error processing chunk: {str(e)}")
                
                await asyncio.sleep(1)
            
            return detailed_messages
        
        except Exception as error:
            print(f"Error in fetch_recent_emails: {error}")
            return []

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _fetch_message_detail(self, message_id):
        """Fetch single message details with retry."""
        try:
            get_message = partial(
                self.service.users().messages().get(
                    userId="me",
                    id=message_id,
                    format='full'
                ).execute
            )
            return await self._safe_api_call(get_message)
        except Exception as e:
            print(f"Error fetching message {message_id}: {str(e)}")
            return None

    async def fetch_draft_replies(self):
        """Fetch all draft email replies."""
        try:
            loop = asyncio.get_event_loop()
            drafts = await loop.run_in_executor(
                None,
                lambda: self.service.users().drafts().list(userId="me").execute()
            )
            
            draft_list = drafts.get("drafts", [])
            return [
                {
                    "draft_id": draft["id"],
                    "threadId": draft["message"]["threadId"],
                    "id": draft["message"]["id"],
                }
                for draft in draft_list
            ]

        except Exception as error:
            print(f"An error occurred while fetching drafts: {error}")
            return []

    async def create_draft_reply(self, initial_email, reply_text):
        """Create a draft reply."""
        try:
            message = await self._create_reply_message(initial_email, reply_text)
            
            loop = asyncio.get_event_loop()
            draft = await loop.run_in_executor(
                None,
                lambda: self.service.users().drafts().create(
                    userId="me",
                    body={"message": message}
                ).execute()
            )

            return draft
        except Exception as error:
            print(f"An error occurred while creating draft: {error}")
            return None

    async def send_reply(self, initial_email, reply_text):
        """Send a reply."""
        try:
            message = await self._create_reply_message(initial_email, reply_text, send=True)
            
            loop = asyncio.get_event_loop()
            sent_message = await loop.run_in_executor(
                None,
                lambda: self.service.users().messages().send(
                    userId="me",
                    body=message
                ).execute()
            )
            
            return sent_message

        except Exception as error:
            print(f"An error occurred while sending reply: {error}")
            return None

    async def _get_email_info(self, msg_id):
        """Get email information asynchronously."""
        try:
            loop = asyncio.get_event_loop()
            message = await loop.run_in_executor(
                None,
                lambda: self.service.users().messages().get(
                    userId="me",
                    id=msg_id,
                    format="full"
                ).execute()
            )

            payload = message.get('payload', {})
            headers = {header["name"].lower(): header["value"] for header in payload.get("headers", [])}
            
            labels = message.get('labelIds', [])
            is_unread = 'UNREAD' in labels
            
            body = await self._get_email_body(payload)
            
            return {
                "id": msg_id,
                "threadId": message.get("threadId"),
                "messageId": headers.get("message-id"),
                "references": headers.get("references", ""),
                "sender": headers.get("from", "Unknown"),
                "subject": headers.get("subject", "No Subject"),
                "body": body,
                "isUnread": is_unread,
                "labels": labels
            }
        except Exception as e:
            print(f"Error getting email info for {msg_id}: {str(e)}")
            return None

    async def _should_skip_email(self, email_info):
        """Check if email should be skipped."""
        return os.environ['MY_EMAIL'] in email_info['sender']

    async def _create_reply_message(self, email, reply_text, send=False):
        """Create reply message."""
        message = await self._create_html_email_message(
            recipient=email.sender,
            subject=email.subject,
            reply_text=reply_text
        )

        if email.messageId:
            message["In-Reply-To"] = email.messageId
            message["References"] = f"{email.references} {email.messageId}".strip()
            
            if send:
                message["Message-ID"] = f"<{uuid.uuid4()}@gmail.com>"
                
        return {
            "raw": base64.urlsafe_b64encode(message.as_bytes()).decode(),
            "threadId": email.threadId
        }

    async def _get_email_body(self, payload):
        """Extract email body asynchronously."""
        if 'parts' in payload:
            body = await self._extract_body(payload['parts'])
        else:
            data = payload['body'].get('data', '')
            body = self._decode_data(data)
            if payload.get('mimeType') == 'text/html':
                body = await self._extract_main_content_from_html(body)

        return await self._clean_body_text(body)

    async def _extract_body(self, parts):
        """Extract body from parts asynchronously."""
        for part in parts:
            mime_type = part.get('mimeType', '')
            data = part['body'].get('data', '')
            if mime_type == 'text/plain':
                return self._decode_data(data)
            if mime_type == 'text/html':
                html_content = self._decode_data(data)
                return await self._extract_main_content_from_html(html_content)
            if 'parts' in part:
                result = await self._extract_body(part['parts'])
                if result:
                    return result
        return ""

    def _decode_data(self, data):
        """Decode base64 data."""
        return base64.urlsafe_b64decode(data).decode('utf-8').strip() if data else ""

    async def _extract_main_content_from_html(self, html_content):
        """Extract content from HTML asynchronously."""
        soup = BeautifulSoup(html_content, 'html.parser')
        for tag in soup(['script', 'style', 'head', 'meta', 'title']):
            tag.decompose()
        return soup.get_text(separator='\n', strip=True)

    async def _clean_body_text(self, text):
        """Clean body text asynchronously."""
        return re.sub(r'\s+', ' ', text.replace('\r', '').replace('\n', '')).strip()

    async def _create_html_email_message(self, recipient, subject, reply_text):
        """Create HTML email message asynchronously."""
        message = MIMEMultipart("alternative")
        message["to"] = recipient
        message["subject"] = f"Re: {subject}" if not subject.startswith("Re: ") else subject

        html_text = reply_text.replace("\n", "<br>").replace("\\n", "<br>")
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body>{html_text}</body>
        </html>
        """

        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        return message

    def _get_gmail_service(self):
        """Initialize Gmail service with extended timeout."""
        try:
            creds = None
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', 
                        SCOPES,
                        redirect_uri='http://localhost:8080/'
                    )
                    creds = flow.run_local_server(port=8080)
                
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            
            # Build service with custom settings
            return build(
                'gmail', 
                'v1', 
                credentials=creds,
                cache_discovery=False,
                
            )
        except Exception as e:
            print(f"Error initializing Gmail service: {str(e)}")
            raise