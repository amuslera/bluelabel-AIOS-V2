#!/usr/bin/env python3
"""Authenticate with the existing Gmail API"""
import webbrowser
import urllib.parse

# The authentication URL from the API response
auth_url = "https://accounts.google.com/o/oauth2/v2/auth?client_id=387555905237-u0uro845dh0jj34o34fggk4om6avnh3g.apps.googleusercontent.com&redirect_uri=http%3A%2F%2Flocalhost%3A8081%2Fgateway%2Fgoogle%2Fcallback&response_type=code&scope=https%3A%2F%2Fmail.google.com%2F+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fgmail.modify+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fgmail.readonly+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fgmail.send&access_type=offline&prompt=consent&include_granted_scopes=true"

# Decode the URL for readability
decoded_url = urllib.parse.unquote(auth_url)

print("Gmail Authentication Required")
print("============================\n")
print("The existing API server needs to be authenticated with Google.")
print("\nOpening browser to authenticate...")
print("\nIf the browser doesn't open, visit this URL manually:")
print(decoded_url)
print("\nAfter authenticating, you'll be redirected to:")
print("http://localhost:8081/gateway/google/callback")
print("\nThe existing API will handle the callback and save the authentication.")

# Open the URL in the default browser
webbrowser.open(auth_url)