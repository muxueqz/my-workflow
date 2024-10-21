import imaplib
import email
from email.header import decode_header
import re
from pocket import Pocket
import os

# Set up IMAP connection
imap_server = os.environ.get("IMAP_SERVER")
imap_username = os.environ.get("IMAP_USERNAME")
imap_password = os.environ.get("IMAP_PASSWORD")
imap = imaplib.IMAP4_SSL(imap_server)
r, s = imap.login(imap_username, imap_password)

print(r, s)
r, s = imap.xatom('ID', '("name" "workflow" "version" "1.0" "vendor" "workflow")')
print(r, s)
r, s = imap.select("INBOX")
print(r, s)

# Set up Pocket connection
pocket_consumer_key = os.environ.get("POCKET_CONSUMER_KEY")
pocket_access_token = os.environ.get("POCKET_ACCESS_TOKEN")
pocket_instance = Pocket(pocket_consumer_key, pocket_access_token)

# Search for unread messages with the specified recipient
recipient_email = os.environ.get("POCKET_RECIPIENT_EMAIL")
search_criteria = 'UNSEEN'
status, messages = imap.search(None, search_criteria)
messages = messages[0].split(b' ')
for message in messages:
    if message == b'':
        continue
    _, msg = imap.fetch(message, "(RFC822)")
    email_message = email.message_from_bytes(msg[0][1])
    if email_message.is_multipart():
        for part in email_message.walk():
            if part.get_content_type() == 'text/plain':
                message_body = part.get_payload(decode=True).decode()
    else:
        message_body = email_message.get_payload(decode=True).decode()
    to_ = email_message.get("To")
    print(f"To: {to_}")
    if f"{recipient_email}" not in to_:
        continue
    # Extract URL from message
    url_regex = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    urls = re.findall(url_regex, message_body)
    for url in urls:
        # Add URL to Pocket
        pocket_instance.add(url)

# Clean up
imap.close()
imap.logout()
