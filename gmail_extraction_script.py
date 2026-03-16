import imaplib
import email
import os
import re
import json
import pandas as pd
import dotenv


dotenv.load_dotenv()
IMAP_SERVER = "imap.gmail.com"
EMAIL_ACCOUNT = os.getenv("mail_@")
PASSWORD = os.getenv("mail_code")
OUTPUT_FOLDER = "emails_output"


def remove_html_tags(text):
    """Removes HTML tags from a string."""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def get_body(msg):
    """Extracts text. Prioritizes 'text/plain', falls back to cleaned HTML."""
    body_plain = None
    body_html = None

    if msg.is_multipart():
        for part in msg.walk():
            # Skip parts that are explicitly marked as attachments
            if "attachment" in str(part.get("Content-Disposition")):
                continue

            try:
                payload = part.get_payload(decode=True)
                if not payload: continue
                decoded_text = payload.decode(errors="ignore")

                if part.get_content_type() == "text/plain":
                    body_plain = decoded_text
                elif part.get_content_type() == "text/html":
                    body_html = decoded_text
            except:
                pass
    else:
        try:
            payload = msg.get_payload(decode=True)
            text = payload.decode(errors="ignore") if payload else ""
            if msg.get_content_type() == "text/html":
                body_html = text
            else:
                body_plain = text
        except:
            pass

    if body_plain:
        return body_plain
    elif body_html:
        return remove_html_tags(body_html)
    else:
        return ""


def save_attachments(msg, email_uid, base_folder="emails_output"):
    """Saves attachments (including images) to a subfolder and returns a list of info about them."""
    attachments_info = []
    attach_folder = os.path.join(base_folder, "attachments", email_uid)
    images_folder = os.path.join(base_folder, "images", email_uid)

    if not msg.is_multipart():
        return attachments_info

    for part in msg.walk():
        content_disposition = str(part.get("Content-Disposition", ""))
        content_type = part.get_content_type()

        # Check if it's an attachment OR an inline image
        is_attachment = "attachment" in content_disposition
        is_inline_image = content_type.startswith("image/")

        if is_attachment or is_inline_image:
            filename = part.get_filename()
            if not filename:
                # Generate filename based on content type
                extension = content_type.split('/')[-1] if '/' in content_type else 'bin'
                filename = f"unknown_file_{email_uid}.{extension}"

            payload = part.get_payload(decode=True)
            if not payload:
                continue

            # Determine which folder to use
            if content_type.startswith("image/"):
                os.makedirs(images_folder, exist_ok=True)
                file_path = os.path.join(images_folder, filename)
                file_type = "image"
            else:
                os.makedirs(attach_folder, exist_ok=True)
                file_path = os.path.join(attach_folder, filename)
                file_type = "attachment"

            # Save the file
            with open(file_path, "wb") as f:
                f.write(payload)

            attachments_info.append({
                "filename": filename,
                "content_type": content_type,
                "size_bytes": len(payload),
                "file_type": file_type,
                "path": file_path
            })

    return attachments_info


# --- Main Script ---

mail = imaplib.IMAP4_SSL(IMAP_SERVER)
mail.login(str(EMAIL_ACCOUNT), str(PASSWORD))
mail.select("inbox")

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# Fetch UIDs
_, data = mail.uid("search", None, "ALL")
uids = data[0].split()
last_10_uids = uids[-10:]

print(f" Processing {len(last_10_uids)} emails...\n")

# Load existing Excel data if available
excel_path = os.path.join(OUTPUT_FOLDER, "emails.xlsx")
try:
    existing_df = pd.read_excel(excel_path)
    existing_uids = set(existing_df['UID'].astype(str).tolist())
    print(f"Loaded {len(existing_uids)} existing UIDs from Excel.")
except FileNotFoundError:
    existing_df = pd.DataFrame(columns=['UID', 'Email Content', 'Attachments'])
    existing_uids = set()
    print("No existing Excel file found. Starting fresh.")

# List to hold new Excel data
excel_data = []

for uid in reversed(last_10_uids): 
    _, msg_data = mail.uid("fetch", uid, "(RFC822)")
    msg = email.message_from_bytes(msg_data[0][1])

    email_uid = uid.decode()

    if email_uid in existing_uids:
        print(f"UID {email_uid} already exists, skipping.")
        continue

    # 1. Save attachments and get metadata
    attachments = save_attachments(msg, email_uid, OUTPUT_FOLDER)

    # 2. Get cleaned body
    email_body = get_body(msg)

    # 3. Prepare JSON Data
    email_json = {
        "id": email_uid,
        "from": msg.get("from", "Unknown"),
        "subject": msg.get("subject", "No Subject"),
        "date": msg.get("date", "Unknown Date"),
        "body": email_body.strip(),
        "attachments": attachments  # Added attachment list here
    }

    # Print JSON to console
    print(json.dumps(email_json, indent=4, ensure_ascii=False))
    print("-" * 50)

    # Collect data for Excel
    attachments_str = "; ".join([att['filename'] for att in attachments]) if attachments else ""
    excel_data.append([email_uid, email_body.strip(), attachments_str])

mail.logout()

# Save to Excel if there are new emails
if excel_data:
    new_df = pd.DataFrame(excel_data, columns=['UID', 'Email Content', 'Attachments'])
    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    combined_df.to_excel(excel_path, index=False)
    print(f"\n Process complete. {len(excel_data)} new emails added to {excel_path}")
else:
    print("\n Process complete. No new emails to add.")
