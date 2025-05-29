import imaplib
import email
import re
from email.header import decode_header
import email.utils
from config import IMAP_HOST, IMAP_USER, IMAP_PASS, IMAP_FOLDER, SIEVE_HOST, SIEVE_PORT
from managesieve import MANAGESIEVE

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
        print(f"Folder {folder_name} already exists")
        return True

    status, data = mail.create(folder_name)
    if status == 'OK':
        print(f"Folder {folder_name} created successfully")
        return True
    elif b'ALREADYEXISTS' in data[0]:
        print(f"Folder {folder_name} already exists")
        return True
    else:
        print(f"Error creating folder {folder_name}: {data}")
        return False

def add_sieve_filter(email_address, folder_name):
    try:
        print(f"Connecting to ManageSieve on {SIEVE_HOST}:{SIEVE_PORT}...")
        client = MANAGESIEVE(
            host=SIEVE_HOST,
            port=SIEVE_PORT,
            use_tls=True,
            tls_verify=False
        )
        print("Connected")

        print("Checking capabilities...")
        capabilities = client.capabilities
        print(f"Capabilities: {capabilities}")

        print(f"Logging in as accounts with PLAIN LOGIN auth")
        login = client.login("PLAIN", "accounts", IMAP_PASS)
        print("Logged in: ", login)

        scripts = client.listscripts()
        print(f"Available scripts: {scripts}")

        script_name = "autofolder"
        script_content = ""

        if script_name in scripts:
            script_content = client.getscript(script_name).decode()

        rule = f'''
if address :contains "From" "{email_address}" {{
    fileinto "{folder_name}";
}}
'''

        if rule.strip() in script_content:
            print(f"Sieve rule for {email_address} already exists")
        else:
            new_script = script_content + rule
            client.putscript(script_name, new_script.encode())
            client.setactive(script_name)
            print(f"Sieve rule added for {email_address} → {folder_name}")

        client.logout()
    except Exception as e:
        print(f"Error updating sieve script: {e}")

def fetch_last_emails_and_create_folders():
    mail = imaplib.IMAP4_SSL(IMAP_HOST)
    mail.login(IMAP_USER, IMAP_PASS)
    mail.select(IMAP_FOLDER)

    status, messages = mail.search(None, "ALL")
    if status != "OK":
        print("No messages found!")
        mail.logout()
        return

    msg_nums = messages[0].split()
    last_msgs = msg_nums[-10:]

    for num in last_msgs:
        status, data = mail.fetch(num, '(RFC822)')
        if status != "OK":
            print(f"Failed to fetch message {num}")
            continue

        msg = email.message_from_bytes(data[0][1])
        from_raw = msg.get("From", "")
        from_decoded = decode_mime_words(from_raw)

        sender_email = email.utils.parseaddr(from_decoded)[1]
        if not sender_email:
            print("No valid sender email found, skipping this message.")
            continue

        folder_name = normalize_folder_name(sender_email)
        create_folder_if_not_exists(mail, folder_name)
        add_sieve_filter(sender_email, folder_name)

    mail.logout()

if __name__ == "__main__":
    fetch_last_emails_and_create_folders()
