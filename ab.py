from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64

# Gmail API scope
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Authentication
flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
creds = flow.run_local_server(port=0)

service = build('gmail', 'v1', credentials=creds)

# Email तयार करा
message = MIMEText('Hello Akshada, this is a test email from Gmail API!')
message['to'] = 'receiver@gmail.com'
message['subject'] = 'Test Email from API'

raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

# Email पाठवा
service.users().messages().send(userId='me', body={'raw': raw}).execute()

print("✅ Email sent successfully!")