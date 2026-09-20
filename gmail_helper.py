import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")

# Read-only access is all we need — we never modify or send email
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_gmail_service():
    """
    Returns an authenticated Gmail API client.
    The first time this runs, it will open a browser window asking you to
    log in and approve access. After that, it reuses a saved token.
    """
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)

def fetch_recent_emails(query: str, max_results: int = 10):
    """
    Searches Gmail using the given query (same syntax as Gmail's search bar)
    and returns a list of dicts with subject, sender, date, and a text snippet
    for each matching email.
    """
    service = get_gmail_service()

    results = service.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()

    messages = results.get("messages", [])
    emails = []

    for msg_ref in messages:
        msg = service.users().messages().get(
            userId="me", id=msg_ref["id"], format="metadata",
            metadataHeaders=["Subject", "From", "Date"]
        ).execute()

        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}

        emails.append({
            "id": msg["id"],
            "subject": headers.get("Subject", "(no subject)"),
            "from": headers.get("From", "(unknown sender)"),
            "date": headers.get("Date", "(unknown date)"),
            "snippet": msg.get("snippet", "")
        })

    return emails