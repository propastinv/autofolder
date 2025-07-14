import imaplib
from config import IMAP_HOST, IMAP_USER, IMAP_PASS
import re
from datetime import datetime, timedelta

def clean_all_deleted_and_old():
    mail = imaplib.IMAP4_SSL(IMAP_HOST)
    mail.login(IMAP_USER, IMAP_PASS)

    date_cutoff = (datetime.now() - timedelta(days=60)).strftime("%d-%b-%Y")

    def clean_folder(folder_name):
        print(f"Selecting folder: {folder_name}")
        status, _ = mail.select(folder_name)
        if status != 'OK':
            print(f"Cannot select folder {folder_name}")
            return

        status, data = mail.search(None, 'BEFORE', date_cutoff)
        if status != 'OK':
            print(f"Failed to search in folder {folder_name}")
            return

        msg_nums = data[0].split()
        if msg_nums:
            print(f"Marking {len(msg_nums)} messages older than {date_cutoff} in {folder_name} for deletion")
            for num in msg_nums:
                mail.store(num, '+FLAGS', '\\Deleted')
            mail.expunge()
        else:
            print(f"No messages older than {date_cutoff} in {folder_name}")

        mail.expunge()

    clean_folder("INBOX")

    status, folders = mail.list()
    if status != 'OK':
        print("Failed to list folders.")
        mail.logout()
        return

    for folder in folders:
        folder_str = folder.decode()
        match = re.search(r'"([^"]+)"$', folder_str)
        if match:
            folder_name = match.group(1)
        else:
            folder_name = folder_str.split(' ')[-1].strip('"')

        if folder_name.upper() == "INBOX":
            continue

        clean_folder(folder_name)

    mail.logout()

if __name__ == "__main__":
    clean_all_deleted_and_old()
