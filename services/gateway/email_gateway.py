import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
import os
from dotenv import load_dotenv
from core.config import config
from core.event_bus import EventBus

# Load environment variables
load_dotenv()

class EmailGateway:
    """Gateway for sending and receiving emails"""
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        """Initialize the email gateway"""
        self.host = config.email.host
        self.port = config.email.port
        self.username = config.email.username
        self.password = config.email.password
        self.use_tls = config.email.use_tls
        
        # Connect to event bus if provided
        self.event_bus = event_bus or EventBus()
    
    def send_email(self, to: str, subject: str, body: str, html: bool = False) -> bool:
        """Send an email
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
            html: Whether the body is HTML
            
        Returns:
            True if the email was sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = to
            msg['Subject'] = subject
            
            # Attach body
            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server
            server = smtplib.SMTP(self.host, self.port)
            if self.use_tls:
                server.starttls()
            
            # Login and send
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            
            return True
        
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False
    
    def check_inbox(self, folder: str = 'INBOX', limit: int = 10) -> List[Dict[str, Any]]:
        """Check the inbox for new emails
        
        Args:
            folder: The folder to check
            limit: Maximum number of emails to retrieve
            
        Returns:
            List of email data dictionaries
        """
        try:
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(self.host)
            mail.login(self.username, self.password)
            mail.select(folder)
            
            # Search for all emails
            status, data = mail.search(None, 'ALL')
            email_ids = data[0].split()
            
            # Get the latest emails
            latest_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
            
            emails = []
            for email_id in latest_ids:
                status, data = mail.fetch(email_id, '(RFC822)')
                raw_email = data[0][1]
                
                # Parse email
                msg = email.message_from_bytes(raw_email)
                
                # Extract content
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = msg.get_payload(decode=True).decode()
                
                # Create email data
                email_data = {
                    "id": email_id.decode(),
                    "from": msg["From"],
                    "to": msg["To"],
                    "subject": msg["Subject"],
                    "date": msg["Date"],
                    "body": body
                }
                
                emails.append(email_data)
            
            mail.close()
            mail.logout()
            
            return emails
        
        except Exception as e:
            print(f"Error checking inbox: {str(e)}")
            return []
    
    def process_incoming_email(self, email_data: Dict[str, Any]) -> str:
        """Process an incoming email and publish to event bus
        
        Args:
            email_data: Email data dictionary
            
        Returns:
            Task ID for the created task
        """
        # Extract data from email
        sender = email_data.get("from", "")
        subject = email_data.get("subject", "")
        body = email_data.get("body", "")
        
        # Extract URL or content from body
        # This is a simple implementation - in a real system, you'd use regex or NLP
        content_source = ""
        for line in body.split("\n"):
            line = line.strip()
            if line.startswith("http"):
                content_source = line
                break
        
        # If no URL found, use the entire body as content
        if not content_source:
            content_source = body
        
        # Create event data
        event_data = {
            "source": "email",
            "sender": sender,
            "subject": subject,
            "content_source": content_source,
            "original_body": body
        }
        
        # Publish to event bus
        task_id = self.event_bus.publish(
            stream="gateway.email",
            event_type="new_content",
            data=event_data
        )
        
        return task_id
    
    def start_email_listener(self, check_interval: int = 60) -> None:
        """Start listening for new emails
        
        Args:
            check_interval: How often to check for new emails (seconds)
        """
        import time
        import threading
        
        def listener_thread():
            last_processed_ids = set()
            
            while True:
                try:
                    # Check inbox
                    emails = self.check_inbox()
                    
                    # Process new emails
                    for email_data in emails:
                        email_id = email_data.get("id")
                        
                        # Skip already processed emails
                        if email_id in last_processed_ids:
                            continue
                        
                        # Process email
                        self.process_incoming_email(email_data)
                        
                        # Add to processed set
                        last_processed_ids.add(email_id)
                    
                    # Limit the size of the processed set
                    if len(last_processed_ids) > 100:
                        last_processed_ids = set(list(last_processed_ids)[-100:])
                    
                except Exception as e:
                    print(f"Error in email listener: {str(e)}")
                
                # Wait before checking again
                time.sleep(check_interval)
        
        # Start listener in a separate thread
        thread = threading.Thread(target=listener_thread, daemon=True)
        thread.start()
