import imaplib
import email
import os
import re
import json

IMAP_SERVER = "imap.gmail.com"
EMAIL_ACCOUNT = "yessineht@gmail.com"
PASSWORD = "aughykyuhihyhgqa"

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
    """Saves attachments to a subfolder and returns a list of info about them."""
    attachments_info = []
    attach_folder = os.path.join(base_folder, "attachments", email_uid)

    if not msg.is_multipart():
        return attachments_info

    for part in msg.walk():
        content_disposition = str(part.get("Content-Disposition", ""))

        if "attachment" in content_disposition:
            # Create folder only if we actually find an attachment
            os.makedirs(attach_folder, exist_ok=True)

            filename = part.get_filename()
            if not filename:
                filename = f"unknown_file_{email_uid}"

            payload = part.get_payload(decode=True)
            if not payload:
                continue

            file_path = os.path.join(attach_folder, filename)

            # Save the file
            with open(file_path, "wb") as f:
                f.write(payload)

            attachments_info.append({
                "filename": filename,
                "content_type": part.get_content_type(),
                "size_bytes": len(payload)
            })

    return attachments_info


# --- Main Script ---

mail = imaplib.IMAP4_SSL(IMAP_SERVER)
mail.login(EMAIL_ACCOUNT, PASSWORD)
mail.select("inbox")

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# Fetch UIDs
_, data = mail.uid("search", None, "ALL")
uids = data[0].split()
last_10_uids = uids[-10:]

print(f"🚀 Processing {len(last_10_uids)} emails...\n")

for uid in reversed(last_10_uids):
    _, msg_data = mail.uid("fetch", uid, "(RFC822)")
    msg = email.message_from_bytes(msg_data[0][1])

    email_uid = uid.decode()

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

    # 4. Save individual TXT file
    filename = os.path.join(OUTPUT_FOLDER, f"email_{email_uid}.txt")
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"UID: {email_uid}\n")
            f.write(f"From: {email_json['from']}\n")
            f.write(f"Subject: {email_json['subject']}\n")
            f.write(f"Date: {email_json['date']}\n")
            f.write(f"Attachments: {len(attachments)}\n")
            f.write("-" * 50 + "\n")
            f.write(email_body)
    except Exception as e:
        print(f"Error saving TXT: {e}")

mail.logout()
print("\n✅ Process complete.")