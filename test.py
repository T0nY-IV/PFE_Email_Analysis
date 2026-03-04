import imaplib  # Import library for IMAP protocol
import email  # Import library to manage email messages
import os  # Import library for operating system tasks (folders/files)
import re  # Import library for regular expressions (HTML stripping)
import json  # Import library to handle JSON data

IMAP_SERVER = "imap.gmail.com"  # Define the Gmail IMAP server address
EMAIL_ACCOUNT = "yessineht@gmail.com"  # Define the target email account
PASSWORD = "aughykyuhihyhgqa"  # Define the password (use App Password)

OUTPUT_FOLDER = "emails_output"  # Define the main folder for output files


def remove_html_tags(text):  # Define function to clean HTML
    clean = re.compile('<.*?>')  # Create a pattern to match anything inside <>
    return re.sub(clean, '', text)  # Replace matched patterns with empty string


def get_body(msg):  # Define function to extract text body
    body_plain = None  # Initialize variable for plain text
    body_html = None  # Initialize variable for HTML text

    if msg.is_multipart():  # Check if email has multiple parts
        for part in msg.walk():  # Loop through every part of the email
            content_disposition = str(part.get("Content-Disposition"))  # Get disposition info
            if "attachment" in content_disposition:  # Skip if it is a file attachment
                continue  # Go to the next part

            try:  # Start error handling for decoding
                payload = part.get_payload(decode=True)  # Download and decode the part content
                if not payload: continue  # Skip if content is empty
                decoded_text = payload.decode(errors="ignore")  # Convert bytes to string

                if part.get_content_type() == "text/plain":  # Check if part is plain text
                    body_plain = decoded_text  # Store as plain text
                elif part.get_content_type() == "text/html":  # Check if part is HTML
                    body_html = decoded_text  # Store as HTML text
            except:  # If decoding fails
                pass  # Ignore the error and move on
    else:  # If email is a single part
        try:  # Start error handling
            payload = msg.get_payload(decode=True)  # Get the content
            text = payload.decode(errors="ignore") if payload else ""  # Decode content
            if msg.get_content_type() == "text/html":  # Check if it's HTML
                body_html = text  # Store as HTML
            else:  # Otherwise
                body_plain = text  # Store as plain text
        except:  # If error occurs
            pass  # Move on

    if body_plain:  # If plain text was found
        return body_plain  # Return it
    elif body_html:  # If only HTML was found
        return remove_html_tags(body_html)  # Return cleaned HTML
    else:  # If nothing found
        return ""  # Return empty string


def save_attachments(msg, email_uid, base_folder="emails_output"):  # Define function for files
    attachments_info = []  # Initialize list for file metadata
    attach_folder = os.path.join(base_folder, "attachments", email_uid)  # Define path for this email's files

    if not msg.is_multipart():  # If email isn't multipart, it has no files
        return attachments_info  # Return empty list

    for part in msg.walk():  # Loop through every part of the email
        content_type = part.get_content_type()  # Get the type (e.g., image/jpeg)
        filename = part.get_filename()  # Try to get the filename

        # FIX: Check for filename OR check if it's an image/application type
        if filename or (content_type.startswith('image/') or content_type.startswith(
                'application/')):  # If it looks like a file
            os.makedirs(attach_folder, exist_ok=True)  # Create the folder if it doesn't exist

            if not filename:  # If the file has no name (common with inline images)
                ext = content_type.split('/')[-1]  # Get extension from content type (e.g., png)
                filename = f"inline_image_{email_uid}.{ext}"  # Create a generic name

            payload = part.get_payload(decode=True)  # Download the file data
            if not payload:  # If data is empty
                continue  # Skip to next part

            file_path = os.path.join(attach_folder, filename)  # Build full path for saving

            with open(file_path, "wb") as f:  # Open file in write-binary mode
                f.write(payload)  # Save the file data

            attachments_info.append({  # Add file details to the list
                "filename": filename,  # Store name
                "content_type": content_type,  # Store type
                "size_bytes": len(payload)  # Store size
            })

    return attachments_info  # Return the full list of files found


mail = imaplib.IMAP4_SSL(IMAP_SERVER)  # Connect to the server using SSL
mail.login(EMAIL_ACCOUNT, PASSWORD)  # Login with credentials
mail.select("inbox")  # Select the inbox folder

if not os.path.exists(OUTPUT_FOLDER):  # Check if output folder exists
    os.makedirs(OUTPUT_FOLDER)  # Create output folder if missing

_, data = mail.uid("search", None, "ALL")  # Search for all email UIDs
uids = data[0].split()  # Split the raw data into a list of UIDs
last_10_uids = uids[-10:]  # Slice the list to get only the last 10

print(f"🚀 Processing {len(last_10_uids)} emails...\n")  # Print progress message

for uid in reversed(last_10_uids):  # Loop through UIDs from newest to oldest
    _, msg_data = mail.uid("fetch", uid, "(RFC822)")  # Fetch the full email content
    msg = email.message_from_bytes(msg_data[0][1])  # Parse the raw bytes into a message object

    email_uid = uid.decode()  # Convert UID bytes to string
    attachments = save_attachments(msg, email_uid, OUTPUT_FOLDER)  # Save all files and images
    email_body = get_body(msg)  # Extract and clean the text body

    email_json = {  # Create a dictionary for the email data
        "id": email_uid,  # Set ID
        "from": msg.get("from", "Unknown"),  # Set Sender
        "subject": msg.get("subject", "No Subject"),  # Set Subject
        "date": msg.get("date", "Unknown Date"),  # Set Date
        "body": email_body.strip(),  # Set Body text
        "attachments": attachments  # Set list of files/images
    }

    print(json.dumps(email_json, indent=4, ensure_ascii=False))  # Print the data as JSON
    print("-" * 50)  # Print a separator line

    filename = os.path.join(OUTPUT_FOLDER, f"email_{email_uid}.txt")  # Define text filename
    try:  # Start error handling for file writing
        with open(filename, "w", encoding="utf-8") as f:  # Open text file for writing
            f.write(f"UID: {email_uid}\n")  # Write UID
            f.write(f"From: {email_json['from']}\n")  # Write Sender
            f.write(f"Subject: {email_json['subject']}\n")  # Write Subject
            f.write(f"Date: {email_json['date']}\n")  # Write Date
            f.write(f"Files Found: {len(attachments)}\n")  # Write count of files
            f.write("-" * 50 + "\n")  # Write separator
            f.write(email_body)  # Write the main message text
    except Exception as e:  # If an error occurs during saving
        print(f"Error saving TXT: {e}")  # Print the error message

mail.logout()  # Log out from the email server
print("\n✅ Process complete.")  # Print final completion message
