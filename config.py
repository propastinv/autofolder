import os
from dotenv import load_dotenv

load_dotenv()

IMAP_HOST = os.getenv("IMAP_HOST", "mail.example.com")
IMAP_USER = os.getenv("IMAP_USER", "autofolder@example.com")
IMAP_PASS = os.getenv("IMAP_PASS", "your-password")
IMAP_FOLDER = os.getenv("IMAP_FOLDER", "INBOX")
SIEVE_HOST = os.getenv("SIEVE_HOST", "mail.example.com")
SIEVE_PORT = os.getenv("SIEVE_PORT", "4190")