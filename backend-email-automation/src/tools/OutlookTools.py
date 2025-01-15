import os
import base64
import requests
from msal import ConfidentialClientApplication
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class OutlookTools:
    def __init__(self, client_id, client_secret, tenant_id):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.token = self._get_access_token()

    def _get_access_token(self):
        """
        Authenticate using MSAL and obtain an access token.
        """
        app = ConfidentialClientApplication(
            self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            client_credential=self.client_secret,
        )

        result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        if "access_token" in result:
            return result["access_token"]
        else:
            raise Exception("Could not obtain access token")

    def _make_request(self, method, endpoint, payload=None):
        """
        Make a request to Microsoft Graph API.
        """
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}{endpoint}"
        response = requests.request(method, url, headers=headers, json=payload)

        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")

    def send_email(self, from_email, to_emails, subject, body):
        """
        Send an email via Microsoft Graph.
        """
        message = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": body,
                },
                "toRecipients": [
                    {"emailAddress": {"address": email}} for email in to_emails
                ],
                "from": {"emailAddress": {"address": from_email}},
            },
            "saveToSentItems": "true",
        }

        return self._make_request("POST", "/me/sendMail", payload=message)

    def draft_email(self, subject, body, to_emails):
        """
        Create a draft email.
        """
        message = {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": body,
            },
            "toRecipients": [
                {"emailAddress": {"address": email}} for email in to_emails
            ],
        }

        return self._make_request("POST", "/me/messages", payload=message)

    def fetch_emails(self, folder="inbox", top=10):
        """
        Fetch recent emails from a specified folder.
        """
        endpoint = f"/me/mailFolders/{folder}/messages?$top={top}&$orderby=receivedDateTime DESC"
        return self._make_request("GET", endpoint)
