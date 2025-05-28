from imap_tools import MailBox, AND
from config import IMAP_HOST, IMAP_USER, IMAP_PASS, IMAP_FOLDER
import re

def normalize_folder_name(email):
    local_part = email.split('@')[0]
    return re.sub(r'[^a-zA-Z0-9_]', '_', local_part)

def create_folder_if_not_exists(mailbox, folder_name):
    folders = [f.name for f in mailbox.folder.list()]
    if folder_name not in folders:
        print(f"Creating: {folder_name}")
        mailbox.folder.create(folder_name)
    else:
        print(f"{folder_name} already exists.")

def fetch_and_create_folders():
    with MailBox(IMAP_HOST).login(IMAP_USER, IMAP_PASS, IMAP_FOLDER) as mailbox:
        print(f"Connected to {IMAP_HOST} as {IMAP_USER}")
        messages = mailbox.fetch(limit=20, reverse=True)

        for msg in messages:
            sender_email = msg.from_
            folder_name = normalize_folder_name(sender_email)

            create_folder_if_not_exists(mailbox, folder_name)

            print(f"From: {sender_email}")
            print(f"Folder: {folder_name}")
            print(f"Subject: {msg.subject}")
            print(f"Date: {msg.date}")
            print("—" * 40)

if __name__ == "__main__":
    fetch_and_create_folders()
