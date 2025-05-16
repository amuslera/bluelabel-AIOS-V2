# Gmail Integration Setup Guide

This guide covers the complete setup process for Gmail integration in Bluelabel AIOS.

## Prerequisites

1. Google Cloud Project with Gmail API enabled
2. OAuth 2.0 credentials (Web application type)
3. Python environment with required packages

## Setup Steps

### 1. Google Cloud Console Configuration

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Enable Gmail API:
   - Go to APIs & Services > Library
   - Search for "Gmail API"
   - Click Enable

### 2. Create OAuth 2.0 Credentials

1. Go to APIs & Services > Credentials
2. Click "+ CREATE CREDENTIALS" > OAuth client ID
3. Choose "Web application"
4. Add authorized redirect URI:
   ```
   http://localhost:8080/gateway/google/callback
   ```
5. Download the JSON credentials file
6. Save as `data/mcp/google_credentials.json`

### 3. Authenticate and Get Token

Run the OAuth authentication script:

```bash
cd /path/to/bluelabel-AIOS-V2
source .venv/bin/activate
python3 scripts/gmail_oauth_server.py
```

This will:
- Start a local server on port 8080
- Open your browser for Google authentication
- Save the token to `data/mcp/gmail_token.json`

### 4. Test the Integration

Run the integration test:

```bash
python3 scripts/test_gmail_integration.py
```

This will test:
- Label listing
- Profile access
- Message fetching
- Email sending

## Troubleshooting

### Port 8080 Already in Use

```bash
# Check what's using port 8080
lsof -i :8080

# Kill the process if needed
kill -9 <PID>
```

### Redirect URI Mismatch

Ensure the redirect URI in your Google Cloud Console exactly matches:
```
http://localhost:8080/gateway/google/callback
```

### Token Expiration

The OAuth token will automatically refresh using the refresh token. If issues persist, re-run the authentication script.

## API Usage

The Gmail gateway is available through the API at:
- Send email: `POST /gateway/send`
- Fetch emails: `GET /gateway/messages`

See the API documentation for full details.

## Token Management

- Token is stored at: `data/mcp/gmail_token.json`
- Credentials are at: `data/mcp/google_credentials.json`
- The gateway automatically handles token refresh

## Environment Variables (Optional)

You can also set these environment variables instead of using the credentials file:
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
