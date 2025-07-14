import imaplib
import email
import re
from email.header import decode_header
import email.utils
from config import IMAP_HOST, IMAP_USER, IMAP_PASS, IMAP_FOLDER

BATCH_SIZE = 100
EMAIL_RE = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')

def decode_mime_words(s):
    decoded = decode_header(s)
    return ''.join([
        part.decode(enc or 'utf-8') if isinstance(part, bytes) else part
        for part, enc in decoded
    ])

def parse_recipients(to_decoded):
    recipients = email.utils.getaddresses([to_decoded])
    valid_recipients = [r for _, r in recipients if r]
    if valid_recipients:
        return valid_recipients

    parts = re.split(r'[,\s]+', to_decoded)
    valid_recipients = [p for p in parts if EMAIL_RE.fullmatch(p)]
    return valid_recipients

def normalize_folder_name(email_address):
    local_part, domain = email_address.split('@', 1)
    if local_part.lower() == "admin":
        domain_part = domain.split('.')[0]
        return re.sub(r'[^a-zA-Z0-9_]', '_', domain_part)
    else:
        return re.sub(r'[^a-zA-Z0-9_]', '_', local_part)


def get_existing_folders(mail):
    status, folders = mail.list()
    if status != 'OK':
        print('Error getting folder list:', folders)
        return set()
    return set(
        f.decode().split(' "/" ')[-1].strip('"') for f in folders
    )

def create_folder_if_not_exists(mail, folder_name, existing_folders):
    if folder_name in existing_folders:
        return True

    status, data = mail.create(folder_name)
    if status == 'OK':
        mail.subscribe(folder_name)
        print(f"Folder {folder_name} created and subscribed")
        existing_folders.add(folder_name)
        return True
    elif data and b'ALREADYEXISTS' in data[0]:
        existing_folders.add(folder_name)
        return True
    else:
        print(f"Error creating folder {folder_name}: {data}")
        return False

def move_message(mail, msg_id, dest_folder):
    res, data = mail.copy(msg_id, dest_folder)
    if res != 'OK':
        print(f"Failed to copy message {msg_id} to {dest_folder}, response: {res}, data: {data}")
        return False
    store_res, store_data = mail.store(msg_id, '+FLAGS', '\\Deleted')
    if store_res != 'OK':
        print(f"Failed to mark message {msg_id} as deleted, response: {store_res}, data: {store_data}")
        return False
    return True

def fetch_unread_and_distribute():
    mail = imaplib.IMAP4_SSL(IMAP_HOST)
    mail.login(IMAP_USER, IMAP_PASS)
    mail.select(IMAP_FOLDER)

    status, messages = mail.search(None, "ALL")
    if status != "OK":
        print("No messages found!")
        mail.logout()
        return

    msg_nums = messages[0].split()
    existing_folders = get_existing_folders(mail)

    total = len(msg_nums)
    print(f"Total messages to process: {total}")

    for i in range(0, total, BATCH_SIZE):
        batch = msg_nums[i:i + BATCH_SIZE]
        print(f"Processing batch {i // BATCH_SIZE + 1} ({len(batch)} messages)...")

        for num in batch:
            num_str = num.decode('utf-8')
            if not num_str.isdigit() or num_str == '0':
                print(f"Invalid message number: {num_str}, skipping")
                continue

            status, data = mail.fetch(num_str, '(BODY.PEEK[])')
            if status != "OK":
                print(f"Failed to fetch message {num_str}")
                continue

            msg = email.message_from_bytes(data[0][1])
            to_raw = msg.get("To", "")
            if not to_raw:
                to_raw = msg.get("X-Forwarded-For", "")
                if not to_raw:
                    print(f"Message {num_str} has no 'To' or 'X-Forwarded-For' header, skipping.")
                    continue

            to_decoded = decode_mime_words(to_raw)
            recipients = parse_recipients(to_decoded)

            if not recipients:
                print(f"Message {num_str} — no valid recipient emails parsed from 'To': {to_raw}")
                continue

            moved = False
            for recipient in recipients:
                if isinstance(recipient, tuple) and len(recipient) == 2:
                    recipient_email = recipient[1]
                else:
                    recipient_email = recipient

                if not recipient_email:
                    continue

                folder_name = normalize_folder_name(recipient_email)
                if create_folder_if_not_exists(mail, folder_name, existing_folders):
                    print(f"Moving message {num_str} to {folder_name}...")
                    if move_message(mail, num_str, folder_name):
                        moved = True

            if not moved:
                print(f"Message {num_str} — failed to move to any recipient folder.")

        mail.expunge()

    mail.logout()

if __name__ == "__main__":
    fetch_unread_and_distribute()
