import imaplib
import email
import re
from pocket import Pocket
import os

# Set up IMAP connection
imap_server = os.environ.get("IMAP_SERVER")
imap_username = os.environ.get("IMAP_USERNAME")
imap_password = os.environ.get("IMAP_PASSWORD")
imap = imaplib.IMAP4_SSL(imap_server)
imap.login(imap_username, imap_password)
imap.select("INBOX", readonly=True)

# Set up Pocket connection
pocket_consumer_key = os.environ.get("POCKET_CONSUMER_KEY")
pocket_access_token = os.environ.get("POCKET_ACCESS_TOKEN")
pocket_instance = Pocket(pocket_consumer_key, pocket_access_token)

# Search for unread messages with the specified recipient
recipient_email = os.environ.get("POCKET_RECIPIENT_EMAIL")
search_criteria = f'(UNSEEN HEADER To {recipient_email})'
status, messages = imap.search(None, search_criteria)
messages = messages[0].split(b' ')
for message in messages:
    _, msg = imap.fetch(message, "(RFC822)")
    email_message = email.message_from_bytes(msg[0][1])
    if email_message.is_multipart():
        for part in email_message.walk():
            if part.get_content_type() == 'text/plain':
                message_body = part.get_payload(decode=True).decode()
    else:
        message_body = email_message.get_payload(decode=True).decode()

    # Extract URL from message
    url_regex = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    urls = re.findall(url_regex, message_body)
    for url in urls:
        # Add URL to Pocket
        pocket_instance.add(url)

# Clean up
imap.close()
imap.logout()
