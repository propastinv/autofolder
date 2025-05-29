import imaplib
import email
import re
from email.header import decode_header
import email.utils
from config import IMAP_HOST, IMAP_USER, IMAP_PASS, IMAP_FOLDER

def decode_mime_words(s):
    decoded = decode_header(s)
    return ''.join([
        part.decode(enc or 'utf-8') if isinstance(part, bytes) else part
        for part, enc in decoded
    ])

def normalize_folder_name(email_address):
    local_part = email_address.split('@')[0]
    return re.sub(r'[^a-zA-Z0-9_]', '_', local_part)

def create_folder_if_not_exists(mail, folder_name):
    status, folders = mail.list()
    if status != 'OK':
        print('Error getting folder list:', folders)
        return False

    folder_names = [f.decode().split(' "/" ')[-1].strip('"') for f in folders]
    if folder_name in folder_names:
        return True

    status, data = mail.create(folder_name)
    if status == 'OK':
        mail.subscribe(folder_name)
        print(f"Folder {folder_name} created and subscribed")
        return True
    elif b'ALREADYEXISTS' in data[0]:
        return True
    else:
        print(f"Error creating folder {folder_name}: {data}")
        return False

def move_message(mail, msg_id, dest_folder):
    res, _ = mail.copy(msg_id, dest_folder)
    if res != 'OK':
        print(f"Failed to copy message {msg_id} to {dest_folder}")
        return False
    mail.store(msg_id, '+FLAGS', '\\Deleted')
    return True

def fetch_unread_and_distribute():
    mail = imaplib.IMAP4_SSL(IMAP_HOST)
    mail.login(IMAP_USER, IMAP_PASS)
    mail.select(IMAP_FOLDER)

    status, messages = mail.search(None, 'UNSEEN')
    if status != "OK":
        print("No unread messages found!")
        mail.logout()
        return

    msg_nums = messages[0].split()

    for num in msg_nums:
        status, data = mail.fetch(num, '(BODY.PEEK[])')
        if status != "OK":
            print(f"Failed to fetch message {num}")
            continue

        msg = email.message_from_bytes(data[0][1])
        from_raw = msg.get("From", "")
        from_decoded = decode_mime_words(from_raw)

        sender_email = email.utils.parseaddr(from_decoded)[1]
        if not sender_email:
            print("No valid sender email found, skipping.")
            continue

        folder_name = normalize_folder_name(sender_email)
        if create_folder_if_not_exists(mail, folder_name):
            print(f"Moving message {num} to {folder_name}...")
            move_message(mail, num, folder_name)

    mail.expunge()
    mail.logout()

if __name__ == "__main__":
    fetch_unread_and_distribute()
