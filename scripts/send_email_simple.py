#!/usr/bin/env python3
"""Simple email sender using SMTP"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def send_email_smtp(to_email, subject, body):
    """Send email using SMTP (simpler approach)"""
    # Get credentials from environment
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME", os.getenv("EMAIL_USERNAME"))
    smtp_password = os.getenv("SMTP_PASSWORD", os.getenv("EMAIL_PASSWORD"))
    
    if not smtp_username or not smtp_password:
        print("Error: SMTP credentials not configured")
        print("Please set in .env:")
        print("  SMTP_USERNAME=your-email@gmail.com")
        print("  SMTP_PASSWORD=your-app-password")
        print("\nFor Gmail, you need an App Password:")
        print("1. Go to https://myaccount.google.com/apppasswords")
        print("2. Generate an app password for 'Mail'")
        print("3. Use that password in SMTP_PASSWORD")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect and send
        print(f"Connecting to {smtp_server}:{smtp_port}")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        
        print(f"Sending email to {to_email}")
        server.send_message(msg)
        server.quit()
        
        print("✓ Email sent successfully!")
        return True
        
    except Exception as e:
        print(f"Error sending email: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you're using an App Password, not your regular password")
        print("2. Enable 2-factor authentication on your Google account")
        print("3. Check that 'Less secure app access' is not needed (App Passwords bypass this)")
        return False


def main():
    """Test email sending"""
    print("Simple Email Sender")
    print("==================\n")
    
    # Test email
    to_email = input("Enter recipient email (or press Enter for self-test): ").strip()
    if not to_email:
        to_email = os.getenv("SMTP_USERNAME", "test@example.com")
    
    subject = f"Test Email - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    body = """This is a test email sent using SMTP.

If you receive this, your email configuration is working correctly.

This bypasses OAuth complexity and uses App Passwords for Gmail.
"""
    
    print(f"\nSending test email to: {to_email}")
    send_email_smtp(to_email, subject, body)


if __name__ == "__main__":
    main()