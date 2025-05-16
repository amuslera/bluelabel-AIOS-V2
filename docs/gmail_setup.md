# Gmail Integration Setup Guide

This guide will help you set up Gmail integration for the Bluelabel AIOS project.

## Prerequisites

1. A Google account
2. Access to Google Cloud Console
3. Python environment with dependencies installed

## Step 1: Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click on it and press "Enable"

## Step 2: Create OAuth 2.0 Credentials

1. In Google Cloud Console, go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Configure the OAuth consent screen if prompted:
   - Choose "External" for user type
   - Fill in the required fields
   - Add your email to test users
4. For Application type, select "Web application"
5. Add authorized redirect URI:
   ```
   http://localhost:9090/auth/callback
   ```
6. Save and download the credentials
7. Note your Client ID and Client Secret

## Step 3: Configure Environment

1. Create or update your `.env` file:
   ```bash
   cp .env.example .env
   ```

2. Add your Google OAuth credentials:
   ```
   GOOGLE_CLIENT_ID=your_client_id_here
   GOOGLE_CLIENT_SECRET=your_client_secret_here
   ```

## Step 4: Run the OAuth Test

1. Activate your virtual environment:
   ```bash
   source .venv/bin/activate
   ```

2. Run the full Gmail test:
   ```bash
   python3 scripts/test_gmail_full.py
   ```

3. Follow the prompts:
   - A browser window will open
   - Log in to your Google account
   - Grant permissions for Gmail access
   - You'll be redirected to localhost:9090
   - The script will save the authentication token

## Step 5: Test the API

1. Start the API server:
   ```bash
   uvicorn apps.api.main:app --reload
   ```

2. In another terminal, run the API test:
   ```bash
   python3 scripts/test_email_api.py
   ```

## Available Endpoints

Once configured, you can use these endpoints:

- `GET /api/v1/communication/communication/status/email` - Check email status
- `GET /api/v1/communication/communication/fetch?channel=email&limit=10` - Fetch emails
- `POST /api/v1/communication/communication/send` - Send email
  ```json
  {
    "channel": "email",
    "to": "recipient@example.com",
    "subject": "Test Subject",
    "body": "Email body text"
  }
  ```
- `GET /api/v1/communication/communication/metrics` - Get metrics

## Token Management

- The OAuth token is saved to `data/gmail_token.json`
- It will be automatically refreshed when needed
- To re-authenticate, delete the token file and run the test again

## Troubleshooting

1. **"Missing environment variables" error**:
   - Make sure your `.env` file contains the Google OAuth credentials

2. **"Gmail service not initialized" error**:
   - Run the OAuth test first to authenticate

3. **Browser doesn't open**:
   - Manually visit the URL shown in the console
   - Make sure port 9090 is not in use

4. **Permission denied errors**:
   - Ensure the Gmail API is enabled in Google Cloud Console
   - Check that your OAuth scopes include Gmail access

## Security Notes

- Never commit your `.env` file or credentials to version control
- The token file contains sensitive data - keep it secure
- Use environment variables for production deployments
- Rotate credentials regularly