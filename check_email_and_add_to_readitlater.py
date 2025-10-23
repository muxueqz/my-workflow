import imaplib
import email
from email.header import decode_header
import re
import os
from supabase import create_client, Client

# --- IMAP setup ---
imap_server = os.environ.get("IMAP_SERVER")
imap_username = os.environ.get("IMAP_USERNAME")
imap_password = os.environ.get("IMAP_PASSWORD")

imap = imaplib.IMAP4_SSL(imap_server)
r, s = imap.login(imap_username, imap_password)
print("Login:", r, s)

r, s = imap.xatom('ID', '("name" "workflow" "version" "1.0" "vendor" "workflow")')
print("ID:", r, s)

r, s = imap.select("INBOX")
print("Select INBOX:", r, s)

# --- Supabase setup ---
supabase_url = os.environ.get("SUPABASE_URL")
supabase_table = os.environ.get("SUPABASE_TABLE")
supabase_key = os.environ.get("SUPABASE_KEY")  # use service role key for insert access
supabase: Client = create_client(supabase_url, supabase_key)

# --- Email processing ---
recipient_email = os.environ.get("RECIPIENT_EMAIL")  # new env var for recipient
search_criteria = 'UNSEEN'
status, messages = imap.search(None, search_criteria)
messages = messages[0].split(b' ')

for message in messages:
    if message == b'':
        continue
    _, msg = imap.fetch(message, "(RFC822)")
    email_message = email.message_from_bytes(msg[0][1])

    # Extract plain text content
    if email_message.is_multipart():
        for part in email_message.walk():
            if part.get_content_type() == 'text/plain':
                message_body = part.get_payload(decode=True).decode(errors='ignore')
                break
    else:
        message_body = email_message.get_payload(decode=True).decode(errors='ignore')

    to_ = email_message.get("To")
    print(f"To: {to_}")
    if f"{recipient_email}" not in to_:
        continue

    # Extract URLs
    url_regex = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    urls = re.findall(url_regex, message_body)
    print(f"Found URLs: {urls}")

    # --- Insert URLs into Supabase ---
    for url in urls:
        try:
            data = {"url": url, "status": "pending"}
            response = supabase.table(supabase_table).insert(data).execute()
            print(f"Inserted into Supabase: {url} → {response}")
        except Exception as e:
            print(f"Error inserting {url}: {e}")

# --- Clean up ---
imap.close()
imap.logout()
print("Done.")
