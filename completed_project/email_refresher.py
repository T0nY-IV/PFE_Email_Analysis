import imaplib
import email
import os
import re
import json
import time
import pandas as pd
import dotenv
from completed_project.mail_analyser import loop_through_emails_and_send_requests, initialize_rag_system
from completed_project.cp_api_methodes import get_last_excel_uid


# Load credentials from the .env file (keeps secrets out of code).
dotenv.load_dotenv()
IMAP_SERVER = "imap.gmail.com"
EMAIL_ACCOUNT = os.getenv("mail_@")
PASSWORD = os.getenv("mail_code")

# Output folder for exported content.
OUTPUT_FOLDER = "emails_output"
# How often to check the mailbox (seconds). Can be overridden via env var.
POLL_INTERVAL_SECONDS = 60


def remove_html_tags(text):
    """Strip HTML tags from a string."""
    clean = re.compile("<.*?>")
    return re.sub(clean, "", text)


def get_body(msg):
    """Extract the email body. Prefer plain text, fall back to HTML."""
    body_plain = None
    body_html = None

    if msg.is_multipart():
        for part in msg.walk():
            # Skip attachments.
            if "attachment" in str(part.get("Content-Disposition")):
                continue

            try:
                payload = part.get_payload(decode=True)
                if not payload:
                    continue
                decoded_text = payload.decode(errors="ignore")

                if part.get_content_type() == "text/plain":
                    body_plain = decoded_text
                elif part.get_content_type() == "text/html":
                    body_html = decoded_text
            except Exception:
                pass
    else:
        try:
            payload = msg.get_payload(decode=True)
            text = payload.decode(errors="ignore") if payload else ""
            if msg.get_content_type() == "text/html":
                body_html = text
            else:
                body_plain = text
        except Exception:
            pass

    if body_plain:
        return body_plain
    if body_html:
        return remove_html_tags(body_html)
    return ""


def save_attachments(msg, email_uid, base_folder=OUTPUT_FOLDER):
    """Save attachments (and inline images) to disk and return metadata."""
    attachments_info = []
    attach_folder = os.path.join(base_folder, "attachments", email_uid)
    images_folder = os.path.join(base_folder, "images", email_uid)

    if not msg.is_multipart():
        return attachments_info

    for part in msg.walk():
        content_disposition = str(part.get("Content-Disposition", ""))
        content_type = part.get_content_type()

        # Treat real attachments and inline images as files to extract.
        is_attachment = "attachment" in content_disposition
        is_inline_image = content_type.startswith("image/")

        if is_attachment or is_inline_image:
            filename = part.get_filename()
            if not filename:
                # Build a fallback filename if the email doesn't provide one.
                extension = content_type.split("/")[-1] if "/" in content_type else "bin"
                filename = f"unknown_file_{email_uid}.{extension}"

            payload = part.get_payload(decode=True)
            if not payload:
                continue

            # Choose output folder based on file type.
            if content_type.startswith("image/"):
                os.makedirs(images_folder, exist_ok=True)
                file_path = os.path.join(images_folder, filename)
                file_type = "image"
            else:
                os.makedirs(attach_folder, exist_ok=True)
                file_path = os.path.join(attach_folder, filename)
                file_type = "attachment"

            # Write the file to disk.
            with open(file_path, "wb") as f:
                f.write(payload)

            attachments_info.append(
                {
                    "filename": filename,
                    "content_type": content_type,
                    "size_bytes": len(payload),
                    "file_type": file_type,
                    "path": file_path,
                }
            )

    return attachments_info


# ---- Main flow ----




def run_once():
    """One polling cycle: connect, fetch new emails, extract, and update state."""
    # Ensure the output directory exists.
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Read the last processed UID (if any).
    last_uid = get_last_excel_uid()
    new_uids = []

    # Connect to Gmail over IMAP+SSL.
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    try:
        mail.login(str(EMAIL_ACCOUNT), str(PASSWORD))
        mail.select("inbox")

        # Search for new emails since the last UID we processed.
        # If no state exists yet, only process the most recent 10 emails.
        if last_uid is not None and isinstance(last_uid, int) and last_uid > 0:
            _, data = mail.uid("search", None, f"(UID {last_uid + 1}:*)")
            new_uids = data[0].split() if data and data[0] else []
        else:
            _, data = mail.uid("search", None, "ALL")
            all_uids = data[0].split() if data and data[0] else []
            new_uids = all_uids[-10:]

        print(f" Processing {len(new_uids)} new emails...\n")

        # Load existing Excel data if available, so we don't duplicate rows.
        excel_path = os.path.join(OUTPUT_FOLDER, "emails.xlsx")
        try:
            existing_df = pd.read_excel(excel_path)
            existing_uids = set(existing_df["UID"].astype(str).tolist())
            print(f"Loaded {len(existing_uids)} existing UIDs from Excel.")
        except FileNotFoundError:
            existing_df = pd.DataFrame(columns=["UID", "Email Content", "Attachments"])
            existing_uids = set()
            print("No existing Excel file found. Starting fresh.")

        # Collect rows to append.
        excel_data = []

        for uid in new_uids:
            _, msg_data = mail.uid("fetch", uid, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])

            email_uid = uid.decode()
            if email_uid in existing_uids:
                print(f"UID {email_uid} already exists, skipping.")
                continue

            # Extract attachments and message body.
            attachments = save_attachments(msg, email_uid, OUTPUT_FOLDER)
            email_body = msg.get("from", "Unknown")+"\n"+get_body(msg)

            # Log extracted data to console (useful for quick checks).
            email_json = {
                "id": email_uid,
                "from": msg.get("from", "Unknown"),
                "subject": msg.get("subject", "No Subject"),
                "date": msg.get("date", "Unknown Date"),
                "body": email_body.strip(),
                "attachments": attachments,
            }
            print(json.dumps(email_json, indent=4, ensure_ascii=False))
            print("-" * 50)

            # Prepare row for Excel export.
            attachments_str = "; ".join([att["filename"] for att in attachments]) if attachments else ""
            excel_data.append([email_uid, email_body.strip(), attachments_str])

        # Write any new rows to Excel.
        if excel_data:
            new_df = pd.DataFrame(excel_data, columns=["UID", "Email Content", "Attachments"])
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df.to_excel(excel_path, index=False)
            print(f"\n Process complete. {len(excel_data)} new emails added to {excel_path}")
        else:
            print("\n Process complete. No new emails to add.")
    finally:
        # Always attempt to close the connection cleanly.
        try:
            mail.logout()
        except Exception:
            pass


def main():
    """Run mailbox checks on a fixed interval until the user stops the script."""
    # Sanity check credentials before starting the loop.
    if not EMAIL_ACCOUNT or not PASSWORD:
        raise ValueError("Missing credentials. Set mail_@ and mail_code in your .env file.")

    print(f"Mailbox watcher started. Polling every {POLL_INTERVAL_SECONDS} seconds.")

    try:
        initialize_rag_system()
        while True:
            print(time.strftime("[%Y-%m-%d %H:%M:%S] Checking for new emails..."))
            run_once()
            print(f"Sleeping for {POLL_INTERVAL_SECONDS} seconds...\n")
            loop_through_emails_and_send_requests()  # Call the function to process emails and send requests to the API
            time.sleep(POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("Mailbox watcher stopped by user.")


if __name__ == "__main__":
    main()
