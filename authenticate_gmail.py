#!/usr/bin/env python3
"""Simple Gmail authentication script"""
import webbrowser
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Check if credentials are set
if not os.getenv("GOOGLE_CLIENT_ID") or not os.getenv("GOOGLE_CLIENT_SECRET"):
    print("Error: Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env file")
    exit(1)

# Build the authorization URL
client_id = os.getenv("GOOGLE_CLIENT_ID")
redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "urn:ietf:wg:oauth:2.0:oob")
scopes = "https://www.googleapis.com/auth/gmail.readonly+https://www.googleapis.com/auth/gmail.send+https://www.googleapis.com/auth/gmail.modify"

auth_url = f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope={scopes}&access_type=offline&prompt=consent"

print("Gmail Authentication")
print("===================")
print()
print("Opening browser to authorize Gmail access...")
print()

# Open the URL in the default browser
webbrowser.open(auth_url)

print("After authorizing, you'll see an authorization code.")
print("Copy the code and run:")
print()
print("  python3 scripts/gmail_auth_with_code.py YOUR_CODE_HERE")
print()
print("If the browser didn't open, visit this URL manually:")
print(auth_url)