# Team Update: OAuth Authentication Implementation

**Date**: February 5, 2026  
**Implemented by**: Mahad  
**Repository**: https://github.com/amasoo280/senior-design

---

## What Changed

I've implemented **Google OAuth 2.0 authentication** to replace the old username/password login system. Here's what's new:

### ✅ New Features

1. **Google Sign-In** - Users now log in with their Google accounts
2. **JWT Tokens** - Secure session management with JSON Web Tokens
3. **User Database** - New `users` table stores user info (email, name, role)
4. **Role-Based Access** - Admin and user roles (ready for future features)
5. **Secure API** - All endpoints now require authentication

### 🔧 Technical Changes

**Backend:**
- Added OAuth packages: `authlib`, `python-jose`, `httpx`
- New files:
  - `backend/app/models.py` - User database model
  - `backend/app/database.py` - Database connection
  - `backend/app/auth.py` - JWT authentication
  - `backend/app/oauth.py` - Google OAuth integration
  - `backend/init_db.py` - Database setup script
- Updated `main.py` with new OAuth endpoints
- Updated `requirements.txt` with new dependencies

**Frontend:**
- Added `@react-oauth/google` package
- Replaced `Login.tsx` with Google Sign-In button
- Updated `App.tsx` to use GoogleOAuthProvider
- Updated `config.ts` with OAuth endpoints
- Updated `auth.ts` utilities for JWT tokens

**Database:**
- New `users` table with columns: id, email, google_id, name, picture, role, created_at, last_login

---

## How to Run the App Locally

### Prerequisites

Before you start, make sure you have:
- Python 3.8+ installed
- Node.js 18+ installed
- MySQL database running
- AWS Bedrock access (we already have this)

### Step 1: Clone the Repository

```bash
git clone git@github.com:amasoo280/senior-design.git
cd senior-design
```

### Step 2: Set Up Google OAuth (ONE PERSON DOES THIS)

**Important**: Only ONE team member needs to create the Google OAuth credentials, then share them with the team.

1. Go to https://console.cloud.google.com/
2. Create a new project: "Sargon AI Chatbot"
3. Enable Google+ API
4. Configure OAuth consent screen:
   - App name: Sargon Partners AI Chatbot
   - Add all team members as test users
5. Create OAuth credentials (Web application):
   - Authorized JavaScript origins: `http://localhost:5173`, `http://localhost:8000`
   - Authorized redirect URIs: `http://localhost:5173`, `http://localhost:8000/auth/google/callback`
6. Copy the **Client ID** and **Client Secret**

**Share these credentials with the team** via a secure channel (not in the Git repo!).

For detailed instructions, see `OAUTH_SETUP.md` in the repo.

### Step 3: Configure Backend

```bash
cd backend

# Create .env file from template
cp env.template .env

# Edit .env with your text editor
```

Fill in these values in `backend/.env`:

```env
# AWS Credentials (we already have these)
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-1

# Database Credentials (contact team for these)
DB_HOST=your_db_host
DB_PORT=3306
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password

# Google OAuth (get from team member who set it up)
GOOGLE_CLIENT_ID=123456789-abc.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abc123

# JWT Secret (generate a new one)
# Run: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=your_generated_secret_here

# Other settings
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
FRONTEND_URL=http://localhost:5173
DEFAULT_TENANT_ID=c55b3c70-7aa7-11eb-a7e8-9b4baf296adf

# Optional: Add your email to become admin automatically
ADMIN_EMAILS=your-email@example.com
```

### Step 4: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 5: Initialize Database

**Only run this ONCE** (coordinate with your team):

```bash
python init_db.py
```

This creates the `users` table in the database.

### Step 6: Configure Frontend

```bash
cd frontend

# Create .env file
cp .env.example .env

# Edit .env
```

Fill in `frontend/.env`:

```env
VITE_GOOGLE_CLIENT_ID=same_as_backend_client_id
VITE_API_BASE_URL=http://localhost:8000
VITE_DEFAULT_TENANT_ID=c55b3c70-7aa7-11eb-a7e8-9b4baf296adf
```

### Step 7: Install Frontend Dependencies

```bash
cd frontend
npm install
```

### Step 8: Start the Backend

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see: `Uvicorn running on http://0.0.0.0:8000`

### Step 9: Start the Frontend

Open a **new terminal window**:

```bash
cd frontend
npm run dev
```

You should see: `Local: http://localhost:5173/`

### Step 10: Test It

1. Open browser: http://localhost:5173
2. Click "Sign in with Google"
3. Select your Google account
4. Grant permissions
5. You should see the chatbot dashboard
6. Try asking a question!

---

## Troubleshooting

### "GOOGLE_CLIENT_ID field required"
**Fix**: Check that `backend/.env` has the Google OAuth credentials

### "Access blocked" when signing in
**Fix**: Make sure you're added as a test user in Google Cloud Console

### Can't see .env file in Windows
**Fix**: Enable hidden files: File Explorer → View → Show → Hidden items

### Database connection error
**Fix**: Check database is running and credentials are correct in `backend/.env`

### Frontend shows blank page
**Fix**: 
1. Check browser console (F12) for errors
2. Make sure backend is running on port 8000
3. Check `VITE_GOOGLE_CLIENT_ID` is set in `frontend/.env`

---

## Important Notes

⚠️ **Never commit `.env` files to Git** - They contain secrets!

✅ **`.env` files are already in `.gitignore`** - Safe to create locally

🔑 **Share credentials securely** - Use a password manager or encrypted message

📧 **Add yourself as test user** - Required in Google Cloud Console OAuth consent screen

---

## Team Coordination

### If you're the first person setting up:
1. ✅ Set up Google OAuth credentials
2. ✅ Share Client ID and Client Secret with team
3. ✅ Run `python init_db.py` to create users table
4. ✅ Add all team members as test users in Google Cloud Console

### If someone already set up:
1. ✅ Get Google OAuth credentials from team
2. ✅ Get database credentials from team
3. ✅ Skip `python init_db.py` (already done)
4. ✅ Start servers and test

---

## Questions?

Check these files in the repo:
- `RUNNING_THE_APP.md` - Detailed setup guide
- `OAUTH_SETUP.md` - Google Cloud Console setup
- `README.md` - Project overview

Or ask me (Mahad) for help!

---

## Summary

**What you need:**
1. Google OAuth credentials (get from team)
2. Database credentials (get from team)
3. Generate your own JWT secret key
4. 30 minutes to set up

**What you'll have:**
- ✅ OAuth authentication working
- ✅ Secure login with Google
- ✅ All existing features working
- ✅ Ready to develop!
