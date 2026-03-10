# Quick Start - Running the App with OAuth

This guide provides step-by-step instructions to get your OAuth-enabled app running.

## Prerequisites Checklist

Before you start, make sure you have:

- [ ] Python 3.8+ installed
- [ ] Node.js 18+ installed
- [ ] MySQL database running and accessible
- [ ] AWS Bedrock credentials
- [ ] Google OAuth credentials (Client ID and Secret from Google Cloud Console)

**If you don't have Google OAuth credentials yet**, follow [OAUTH_SETUP.md](OAUTH_SETUP.md) first.

---

## Step 1: Generate JWT Secret Key

Run this command to generate a secure JWT secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Copy the output** - you'll need it in the next step.

---

## Step 2: Configure Backend Environment

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create `.env` from template:
   ```bash
   cp env.template .env
   ```

3. Edit `.env` and fill in ALL required values:

   ```env
   # AWS Credentials (existing)
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret
   AWS_REGION=us-east-1

   # Database Credentials (existing)
   DB_HOST=your_database_host
   DB_PORT=3306
   DB_NAME=your_database_name
   DB_USER=your_database_user
   DB_PASSWORD=your_database_password

   # Google OAuth (NEW - from Google Cloud Console)
   GOOGLE_CLIENT_ID=123456789-abc123.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=GOCSPX-abc123def456

   # JWT Configuration (NEW - use generated secret from Step 1)
   JWT_SECRET_KEY=paste_your_generated_secret_here
   JWT_ALGORITHM=HS256
   JWT_EXPIRATION_HOURS=24

   # Frontend URL (NEW)
   FRONTEND_URL=http://localhost:5173

   # Admin Emails (NEW - OPTIONAL)
   # Add your email to auto-become admin on first login
   ADMIN_EMAILS=your-email@example.com

   # Tenant ID (existing)
   DEFAULT_TENANT_ID=c55b3c70-7aa7-11eb-a7e8-9b4baf296adf
   ```

---

## Step 3: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**Expected output**: All packages should install successfully, including new OAuth packages (authlib, python-jose, httpx).

---

## Step 4: Initialize Database

This creates the `users` table in your MySQL database:

```bash
python init_db.py
```

**Expected output**:
```
============================================================
Database Initialization Script
============================================================

Database: your_database_name
Host: your_host:3306
User: your_user

Testing database connection...
✓ Database connection successful

Creating database tables...
✓ Database tables created successfully

Current user count: 0

============================================================
```

---

## Step 5: Start Backend Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**✅ Backend is ready!** Leave this terminal running.

---

## Step 6: Configure Frontend Environment

Open a **NEW terminal** window/tab.

1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Create `.env` file:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env`:
   ```env
   # Google OAuth Client ID (SAME as backend)
   VITE_GOOGLE_CLIENT_ID=123456789-abc123.apps.googleusercontent.com

   # Backend API URL
   VITE_API_BASE_URL=http://localhost:8000

   # Tenant ID
   VITE_DEFAULT_TENANT_ID=c55b3c70-7aa7-11eb-a7e8-9b4baf296adf
   ```

---

## Step 7: Install Frontend Dependencies

```bash
cd frontend
npm install
```

**Expected output**: Should install all dependencies including `@react-oauth/google`.

---

## Step 8: Start Frontend Development Server

```bash
npm run dev
```

**Expected output**:
```
  VITE v6.4.0  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

**✅ Frontend is ready!**

---

## Step 9: First Login

1. **Open your browser**: Navigate to `http://localhost:5173`

2. **You'll see the login page** with:
   - Sargon Partners AI logo
   - "Sign in with Google" button

3. **Click "Sign in with Google"**

4. **Google OAuth popup appears**:
   - Select your Google account
   - Review permissions
   - Click "Allow" or "Continue"

5. **You're redirected back to the app**:
   - You should now see the dashboard
   - Your user is created in the database

6. **Verify you're logged in**:
   - Open Browser DevTools (F12)
   - Go to Application → Local Storage
   - You should see `sargon_auth_token` with your JWT

---

## Step 10: Set Yourself as Admin (Optional)

If you didn't add your email to `ADMIN_EMAILS` before logging in, you can manually update the database:

### Option 1: Using MySQL Command Line

```sql
USE your_database_name;
UPDATE users SET role='admin' WHERE email='your-email@example.com';
SELECT * FROM users;  -- Verify the change
```

### Option 2: Using Database GUI (e.g., MySQL Workbench, phpMyAdmin)

1. Connect to your database
2. Find the `users` table
3. Find your user by email
4. Change `role` from `user` to `admin`
5. Save changes

---

## Verification Checklist

After completing all steps, verify everything works:

### ✅ Backend Tests

- [ ] Visit http://localhost:8000 - Should show API info
- [ ] Visit http://localhost:8000/health - Should return `{"status":"healthy"}`
- [ ] Visit http://localhost:8000/db-ping - Should return database ping result

### ✅ Frontend Tests

- [ ] Visit http://localhost:5173 - Should show login page
- [ ] Click "Sign in with Google" - Should open Google OAuth
- [ ] Complete login - Should redirect to dashboard
- [ ] Refresh page - Should stay logged in (token persists)
- [ ] Type a question in chatbot - Should work
- [ ] Click Analytics tab - Should load analytics
- [ ] Click Logs tab - Should load logs
- [ ] Click Logout - Should redirect to login page

### ✅ Database Tests

Check users table:
```sql
SELECT id, email, name, role, created_at, last_login FROM users;
```

You should see your user with:
- Correct email
- Your Google name
- Role (admin or user)
- Timestamps

---

## Troubleshooting

### Backend won't start

**Error**: `GOOGLE_CLIENT_ID field required`

**Solution**: Make sure `backend/.env` has `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`

---

### Frontend shows blank page

**Error**: Check browser console (F12) for errors

**Common fixes**:
1. Make sure backend is running on port 8000
2. Check `frontend/.env` has correct `VITE_GOOGLE_CLIENT_ID`
3. Clear browser cache and reload

---

### "Access blocked" when signing in

**Error**: Google shows "Access blocked: This app's request is invalid"

**Solution**:
1. Go to Google Cloud Console
2. Make sure OAuth consent screen is configured
3. Add yourself as a test user
4. Check redirect URIs are correct

---

### Login button doesn't appear

**Error**: No Google button on login page

**Solution**:
1. Check browser console for errors
2. Verify `VITE_GOOGLE_CLIENT_ID` is set correctly in `frontend/.env`
3. Restart frontend dev server: Stop (`Ctrl+C`) and run `npm run dev` again

---

### Database connection failed

**Error**: `Database connection failed`

**Solution**:
1. Verify database is running
2. Check `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` in `backend/.env`
3. Make sure your database user has permissions to create tables

---

## Quick Reference

### Stop the servers

**Backend**: Press `Ctrl+C` in the backend terminal

**Frontend**: Press `Ctrl+C` in the frontend terminal

### Restart the servers

**Backend**:
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend**:
```bash
cd frontend
npm run dev
```

### View logs

**Backend logs**: Check the terminal where you ran `uvicorn`

**Frontend logs**: Check browser console (F12 → Console tab)

**Application logs**: http://localhost:5173 → Click "Logs" tab (after login)

---

## Next Steps

Now that OAuth is working:

1. **Test the chatbot** - Ask natural language questions
2. **Explore analytics** - View query metrics
3. **Check logs** - See request logs
4. **Add more users** - Invite team members to log in
5. **Customize admin features** - Build admin-only functionality

---

## Summary

You now have a fully functional OAuth-enabled application with:

✅ Google Sign-In authentication
✅ JWT token-based sessions  
✅ Role-based access (admin/user)
✅ Secure API endpoints
✅ Database-backed user management

All your existing AI chatbot functionality works with the new auth system!

---

**Need help?** Check [OAUTH_SETUP.md](OAUTH_SETUP.md) for detailed Google Cloud Console setup or [walkthrough.md](file:///C:/Users/mahad/.gemini/antigravity/brain/4ed55322-155b-4a41-a615-71c81c186e11/walkthrough.md) for technical details.

