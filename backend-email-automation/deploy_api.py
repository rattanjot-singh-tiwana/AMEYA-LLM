from typing import Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langserve import add_routes
from src.graph import Workflow
from dotenv import load_dotenv
from src.tools.GmailTools import GmailToolsClass
from src.tools.enhanced_outlook_tools import EnhancedOutlookTools
from datetime import datetime, timedelta
from collections import defaultdict
import pytz
import os
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load .env file
load_dotenv()

app = FastAPI(
    title="Email Automation",
    version="1.0",
    description="LangGraph backend for the AI email automation workflow",
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

class EmailServiceType(Enum):
    GMAIL = "gmail"
    OUTLOOK = "outlook"

class EmailToolFactory:
    @staticmethod
    def create_email_tool(service_type: EmailServiceType, email_address: str = None):
        try:
            if service_type == EmailServiceType.GMAIL:
                return GmailToolsClass()
            elif service_type == EmailServiceType.OUTLOOK:
                if not all([
                    os.getenv('OUTLOOK_CLIENT_ID'),
                    os.getenv('OUTLOOK_CLIENT_SECRET'),
                    os.getenv('OUTLOOK_TENANT_ID')
                ]):
                    raise ValueError("Missing required Outlook environment variables")
                return EnhancedOutlookTools(email_address)
            else:
                raise ValueError(f"Unsupported email service: {service_type}")
        except Exception as e:
            logger.error(f"Error creating email tool: {str(e)}")
            raise

def detect_service(email_address: str) -> EmailServiceType:
    try:
        email_domain = email_address.lower().split('@')[1]
        if 'gmail.com' in email_domain:
            return EmailServiceType.GMAIL
        elif any(domain in email_domain for domain in ['outlook.com', 'hotmail.com', 'live.com', 'office365.com']):
            return EmailServiceType.OUTLOOK
        return EmailServiceType.GMAIL  # Default to Gmail for custom domains
    except Exception as e:
        logger.error(f"Error detecting email service: {str(e)}")
        return EmailServiceType.GMAIL

# Initialize Email Tools with default email
default_email = os.getenv('DEFAULT_EMAIL')
if not default_email:
    raise ValueError("DEFAULT_EMAIL environment variable must be set")

try:
    current_service = detect_service(default_email)
    email_tools = EmailToolFactory.create_email_tool(current_service, default_email)
except Exception as e:
    logger.error(f"Error initializing email tools: {str(e)}")
    raise

@app.get("/api/email-stats")
async def get_email_stats(
    hours: int = Query(default=24, ge=1, le=720),  # Maximum 30 days
    account: Optional[str] = None
):
    try:
        recent_emails = email_tools.fetch_recent_emails(hours=hours)
        drafts = email_tools.fetch_draft_replies()
        
        if not recent_emails:
            return {
                "total": 0,
                "unread": 0,
                "read": 0,
                "replied": 0,
                "drafted": 0,
                "avgResponse": "0h"
            }
            
        total_emails = len(recent_emails)
        
        # Calculate basic stats
        if current_service == EmailServiceType.GMAIL:
            unread_count = sum(1 for email in recent_emails if 'UNREAD' in email.get('labelIds', []))
            read_count = total_emails - unread_count
            replied_count = sum(1 for email in recent_emails if 'SENT' in email.get('labelIds', []))
        else:
            unread_count = sum(1 for email in recent_emails if not email.get('isRead', True))
            read_count = total_emails - unread_count
            replied_count = sum(1 for email in recent_emails if email.get('hasAttachments', False))
            
        drafted_count = len(drafts)

        # Calculate average response time
        total_response_time = 0
        response_count = 0

        for email in recent_emails:
            if current_service == EmailServiceType.GMAIL:
                # Get received time
                received_time = int(email.get('internalDate', '0')) / 1000  # Convert to seconds
                thread_id = email.get('threadId')
                
                # Find replies in the same thread
                replies = [e for e in recent_emails 
                         if e.get('threadId') == thread_id 
                         and 'SENT' in e.get('labelIds', [])
                         and int(e.get('internalDate', '0')) / 1000 > received_time]
                
                if replies:
                    reply_time = int(replies[0].get('internalDate', '0')) / 1000
                    response_time = reply_time - received_time
                    if response_time > 0:
                        total_response_time += response_time
                        response_count += 1
            else:
                # For Outlook
                if email.get('conversationId') and email.get('receivedDateTime'):
                    received_time = datetime.fromisoformat(email['receivedDateTime'].replace('Z', '+00:00'))
                    replies = [e for e in recent_emails 
                             if e.get('conversationId') == email.get('conversationId')
                             and e.get('from', {}).get('emailAddress', {}).get('address') == default_email
                             and datetime.fromisoformat(e['receivedDateTime'].replace('Z', '+00:00')) > received_time]
                    
                    if replies:
                        reply_time = datetime.fromisoformat(replies[0]['receivedDateTime'].replace('Z', '+00:00'))
                        response_time = (reply_time - received_time).total_seconds()
                        if response_time > 0:
                            total_response_time += response_time
                            response_count += 1

        # Calculate average response time in hours
        avg_response = "0h"
        if response_count > 0:
            avg_hours = round(total_response_time / response_count / 3600, 1)  # Convert seconds to hours
            avg_response = f"{avg_hours}h"

        return {
            "total": total_emails,
            "unread": unread_count,
            "read": read_count,
            "replied": replied_count,
            "drafted": drafted_count,
            "avgResponse": avg_response
        }
    except Exception as e:
        logger.error(f"Error in get_email_stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/email-activity")
async def get_email_activity(
    hours: int = Query(default=24, ge=1, le=720)  # Maximum 30 days
):
    try:
        recent_emails = email_tools.fetch_recent_emails(hours=hours)
        
        activity_data = defaultdict(int)
        current_time = datetime.now(pytz.UTC)
        
        # Initialize all hours with 0
        for hour in range(hours):
            activity_data[hour] = 0
            
        if recent_emails:
            for email in recent_emails:
                try:
                    if current_service == EmailServiceType.GMAIL:
                        email_timestamp = int(email.get('internalDate', '0')) / 1000
                    else:
                        email_timestamp = email.get('receivedDateTime', '')
                        if isinstance(email_timestamp, str):
                            email_time = datetime.fromisoformat(email_timestamp.replace('Z', '+00:00'))
                            email_timestamp = email_time.timestamp()
                    
                    email_time = datetime.fromtimestamp(email_timestamp, pytz.UTC)
                    time_diff = current_time - email_time
                    hours_ago = int(time_diff.total_seconds() / 3600)
                    
                    if 0 <= hours_ago < hours:
                        activity_data[hours_ago] += 1
                except Exception as e:
                    logger.error(f"Error processing email timestamp: {str(e)}")
                    continue
        
        # Create formatted response
        activity = []
        for hour in range(hours - 1, -1, -1):
            time_label = "Now" if hour == 0 else f"{hour}h ago"
            activity.append({
                "time": time_label,
                "emails": activity_data[hour],
                "hour": hour
            })
        
        return activity
        
    except Exception as e:
        logger.error(f"Error in get_email_activity: {str(e)}")
        return []

@app.post("/api/set-email-service")
async def set_email_service(email: str):
    """
    Set the email service for monitoring based on the provided email address.
    """
    try:
        if not email or '@' not in email:
            raise HTTPException(status_code=400, detail="Invalid email address")
            
        service_type = detect_service(email)
        
        # Here you would typically:
        # 1. Validate the email
        # 2. Check credentials
        # 3. Set up monitoring for this account
        
        return {
            "status": "success",
            "message": f"Email service set to {service_type.value} for {email}",
            "service": service_type.value
        }
    except Exception as e:
        logger.error(f"Error setting email service: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")  # Base health check endpoint
async def health_check_base():
    return await health_check()

@app.get("/api/health")  # API prefixed health check endpoint
async def health_check():
    """
    Health check endpoint to verify the API is running and return current email.
    """
    try:
        return {
            "status": "healthy",
            "currentEmail": os.getenv('DEFAULT_EMAIL'),  # Get from environment variable
            "service": current_service.value if current_service else "unknown"
        }
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Add Workflow routes
def get_runnable():
    return Workflow(default_email).app

try:
    runnable = get_runnable()
    add_routes(app, runnable)
except Exception as e:
    logger.error(f"Error adding workflow routes: {str(e)}")
    raise

def main():
    """
    Main function to start the API server.
    """
    try:
        import uvicorn
        logger.info("Starting the API server...")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Error starting the server: {str(e)}")
        raise

if __name__ == "__main__":
    main()