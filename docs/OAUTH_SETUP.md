# Google OAuth Setup Guide

This guide explains how to set up Google OAuth 2.0 credentials for the Sargon Partners AI Chatbot.

## Prerequisites

- A Google account
- Access to [Google Cloud Console](https://console.cloud.google.com/)

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown in the top navigation bar
3. Click "NEW PROJECT"
4. Enter project name: `Sargon Partners AI Chatbot` (or your preferred name)
5. Click "CREATE"
6. Wait for the project to be created, then select it

## Step 2: Enable Google+ API

1. In the Google Cloud Console, go to **APIs & Services** → **Library**
2. Search for "Google+ API"
3. Click on "Google+ API"
4. Click "ENABLE"

*Note: You can also use "Google Identity" API which is the recommended newer option*

## Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **External** user type (unless you have Google Workspace)
3. Click "CREATE"

4. Fill in the App Information:
   - **App name**: `Sargon Partners AI Chatbot`
   - **User support email**: Your email address
   - **App logo**: (Optional) Upload your company logo
   - **Developer contact information**: Your email address

5. Click "SAVE AND CONTINUE"

6. **Scopes** screen:
   - Click "ADD OR REMOVE SCOPES"
   - Add the following scopes:
     - `userinfo.email`
     - `userinfo.profile`
     - `openid`
   - Click "UPDATE" then "SAVE AND CONTINUE"

7. **Test users** (for development):
   - Click "ADD USERS"
   - Add email addresses of users who should be able to test the app
   - Click "ADD" then "SAVE AND CONTINUE"

8. Click "BACK TO DASHBOARD"

## Step 4: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click "+ CREATE CREDENTIALS" at the top
3. Select "OAuth client ID"

4. Configure the OAuth client:
   - **Application type**: Web application
   - **Name**: `Sargon AI Web Client`
   
5. **Authorized JavaScript origins**:
   - Click "ADD URI"
   - Add: `http://localhost:5173` (for development)
   - Add: `http://localhost:3000` (alternative port)
   - Add your production frontend URL when deploying
   
6. **Authorized redirect URIs**:
   - Click "ADD URI"
   - Add: `http://localhost:5173` (for development)
   - Add: `http://localhost:8000/auth/google/callback` (backend callback)
   - Add your production URLs when deploying

7. Click "CREATE"

## Step 5: Save Your Credentials

A dialog will appear with your credentials:

- **Client ID**: Something like `123456789-abc123def456.apps.googleusercontent.com`
- **Client Secret**: Something like `GOCSPX-abc123def456ghi789`

**IMPORTANT**: Copy both values immediately! You'll need them for the next steps.

## Step 6: Configure Backend Environment

1. Navigate to the `backend` directory
2. Create `.env` file from template:
   ```bash
   cp env.template .env
   ```

3. Edit `.env` and add your Google OAuth credentials:
   ```env
   GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your_client_secret_here
   
   # Generate a secure JWT secret (run this command to generate one):
   # python -c "import secrets; print(secrets.token_urlsafe(32))"
   JWT_SECRET_KEY=your_generated_secret_key_here
   
   JWT_ALGORITHM=HS256
   JWT_EXPIRATION_HOURS=24
   FRONTEND_URL=http://localhost:5173
   
   # Optional: Set admin email(s)
   ADMIN_EMAILS=your-email@example.com
   ```

4. Generate a JWT secret key:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
   Copy the output and paste it as `JWT_SECRET_KEY` in your `.env`

## Step 7: Configure Frontend Environment

1. Navigate to the `frontend` directory
2. Create `.env` file:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` and add your Google Client ID:
   ```env
   VITE_GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
   VITE_API_BASE_URL=http://localhost:8000
   VITE_DEFAULT_TENANT_ID=c55b3c70-7aa7-11eb-a7e8-9b4baf296adf
   ```

## Step 8: Test Your Setup

1. Verify your backend `.env` has all required fields:
   - ✓ AWS credentials (for Bedrock)
   - ✓ Database credentials
   - ✓ Google OAuth credentials
   - ✓ JWT secret key

2. Verify your frontend `.env` has:
   - ✓ Google Client ID
   - ✓ API base URL

## Common Issues

### "Access blocked: This app's request is invalid"

- Make sure you've configured the OAuth consent screen
- Verify your redirect URIs match exactly
- Check that you've added your email as a test user (if using External user type)

### "redirect_uri_mismatch"

- Double-check that your redirect URIs in Google Cloud Console match your application URLs exactly
- Don't forget to include both frontend and backend URLs

### Missing GOOGLE_CLIENT_ID in frontend

- Make sure your `.env` file is in the `frontend` directory
- Restart the Vite dev server after changing `.env`
- Verify the variable name starts with `VITE_`

## Security Best Practices

1. **Never commit credentials to Git**:
   - `.env` files are in `.gitignore`
   - Never share your Client Secret publicly

2. **Use different credentials for production**:
   - Create separate OAuth credentials for production
   - Use environment-specific redirect URIs

3. **Rotate JWT secrets regularly**:
   - Generate new JWT secrets periodically
   - Use strong, random secrets (minimum 32 characters)

4. **Limit admin access**:
   - Only add trusted email addresses to `ADMIN_EMAILS`
   - Review admin users regularly

## Next Steps

After completing this setup:

1. Run the database initialization: `python backend/init_db.py`
2. Start the backend server: `cd backend && uvicorn main:app --reload`
3. Start the frontend: `cd frontend && npm run dev`
4. Navigate to `http://localhost:5173` and click "Sign in with Google"

---

For more information:
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Cloud Console](https://console.cloud.google.com/)

