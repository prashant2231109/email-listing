import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
import datetime
from typing import List, Dict, Any, Optional
from bson import ObjectId

from config import EMAIL_HOST, EMAIL_PORT, EMAIL_USERNAME, EMAIL_PASSWORD, IMAP_SERVER, IMAP_PORT
from database import save_email

def decode_email_header(header):
    """Decode email header"""
    decoded_header = decode_header(header)
    header_text = ""
    for part, encoding in decoded_header:
        if isinstance(part, bytes):
            if encoding:
                header_text += part.decode(encoding)
            else:
                header_text += part.decode('utf-8', errors='replace')
        else:
            header_text += part
    return header_text

def get_email_body(msg):
    """Extract email body (text or html)"""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            # Skip attachments
            if "attachment" in content_disposition:
                continue
                
            if content_type == "text/plain":
                return part.get_payload(decode=True).decode('utf-8', errors='replace')
            elif content_type == "text/html":
                return part.get_payload(decode=True).decode('utf-8', errors='replace')
    else:
        return msg.get_payload(decode=True).decode('utf-8', errors='replace')
    
    return ""

def fetch_emails(user_id: str, email_address: str, password: str, 
                 folder: str = "INBOX", limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch emails from IMAP server"""
    try:
        # Connect to IMAP server
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(email_address, password)
        mail.select(folder)
        
        # Search for all emails
        status, messages = mail.search(None, "ALL")
        email_ids = messages[0].split()
        
        # Get the latest emails (limited by 'limit')
        email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
        
        emails = []
        for e_id in email_ids:
            status, msg_data = mail.fetch(e_id, "(RFC822)")
            
            for response in msg_data:
                if isinstance(response, tuple):
                    msg = email.message_from_bytes(response[1])
                    
                    # Get email details
                    subject = decode_email_header(msg["Subject"]) if msg["Subject"] else "No Subject"
                    from_address = decode_email_header(msg["From"]) if msg["From"] else "Unknown"
                    date_str = msg["Date"] if msg["Date"] else None
                    
                    # Parse date
                    if date_str:
                        try:
                            date = email.utils.parsedate_to_datetime(date_str)
                        except:
                            date = datetime.datetime.now()
                    else:
                        date = datetime.datetime.now()
                    
                    # Get email body
                    body = get_email_body(msg)
                    
                    # Create email document
                    email_doc = {
                        "user_id": ObjectId(user_id),
                        "message_id": msg["Message-ID"] if msg["Message-ID"] else str(e_id),
                        "subject": subject,
                        "sender": from_address,
                        "date": date,
                        "body": body,
                        "folder": folder,
                        "read": False,
                        "created_at": datetime.datetime.now()
                    }
                    
                    # Save to database
                    result = save_email(email_doc)
                    
                    # Add ID to document for return
                    email_doc["_id"] = str(result.inserted_id)
                    emails.append(email_doc)
        
        mail.close()
        mail.logout()
        return emails
    
    except Exception as e:
        print(f"Error fetching emails: {str(e)}")
        return []

def send_email(sender: str, password: str, recipient: str, subject: str, body: str, 
               html_body: Optional[str] = None) -> bool:
    """Send email using SMTP"""
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient
        
        # Add text body
        msg.attach(MIMEText(body, "plain"))
        
        # Add HTML body if provided
        if html_body:
            msg.attach(MIMEText(html_body, "html"))
        
        # Connect to SMTP server
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(sender, password)
        
        # Send email
        server.sendmail(sender, recipient, msg.as_string())
        server.quit()
        
        return True
    
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False