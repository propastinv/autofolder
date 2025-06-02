# autofolder

**autofolder** is a Python utility that automatically organizes your emails by moving each message into a dedicated IMAP folder based on the sender's email address. This helps keep your inbox tidy and makes it easier to find emails from specific senders.

## Features

- Connects to your IMAP server and scans all messages in the specified folder.
- Automatically creates folders for each sender (if they don't exist).
- Moves each email to its corresponding sender's folder.
- Designed for easy deployment with Docker.

## Requirements

- IMAP email account
- Docker

## Configuration

Create a `.env` file in the project root with the following variables:

```env
IMAP_HOST=mail.example.com
IMAP_USER=autofolder@example.com
IMAP_PASS=your-password
IMAP_FOLDER=INBOX
```

## Installation & Usage (Docker)

1. **Build the Docker image:**

   ```sh
   docker build -t autofolder .
   ```

2. **Run the container:**

   ```sh
   docker run --env-file .env autofolder
   ```

---

**autofolder** is maintained by propastinv.