# What Goes in .env File - Quick Reference

## ✅ YES - Goes in `.env` file (backend/.env)

These are **credentials and connection details** that should NOT be in code:

### AWS Credentials (Required)
```env
AWS_ACCESS_KEY_ID=your_actual_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_actual_aws_secret_key_here
AWS_REGION=us-east-1
```

### Database Credentials (Required)
```env
DB_HOST=your_database_hostname_or_ip
DB_PORT=3306
DB_USER=your_database_username
DB_PASSWORD=your_database_password
DB_NAME=your_database_name
```

### Optional Settings
```env
# Bedrock Model (optional - has default)
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Default Tenant ID for testing (optional)
DEFAULT_TENANT_ID=your-account-id-here

# Query timeout (optional - defaults to 30 seconds)
DB_QUERY_TIMEOUT_SECONDS=30
```

---

## ❌ NO - Does NOT go in `.env` file

These are **code/configuration** that stay in the codebase:

### Database Schema
- **Location:** `backend/app/schema/context.py`
- **What it is:** Table definitions, column names, relationships
- **Why:** This is code, not credentials. Already updated with your Sargon Partners schema!

### Application Code
- All Python files in `backend/app/`
- All React/TypeScript files in `frontend/src/`
- Configuration logic (like `backend/app/config.py`)

### Frontend Config (Optional)
- **Location:** `frontend/.env` (separate from backend)
- **What:** API URL and tenant ID for frontend
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_DEFAULT_TENANT_ID=default
```

---

## 📝 Quick Setup Checklist

1. **Copy the template:**
   ```bash
   cd backend
   cp env.template .env
   ```

2. **Edit `.env` and fill in:**
   - [ ] AWS_ACCESS_KEY_ID
   - [ ] AWS_SECRET_ACCESS_KEY
   - [ ] AWS_REGION
   - [ ] DB_HOST
   - [ ] DB_PORT
   - [ ] DB_USER
   - [ ] DB_PASSWORD
   - [ ] DB_NAME
   - [ ] (Optional) DEFAULT_TENANT_ID

3. **That's it!** The schema is already configured in code.

---

## 🔒 Security Notes

- ✅ `.env` is in `.gitignore` - won't be committed to git
- ✅ Never commit `.env` file to version control
- ✅ Use `env.template` as a reference (no real credentials)
- ✅ Keep `.env` file secure and private

---

## Example Complete `.env` File

```env
# AWS Bedrock Configuration
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1

# Database Configuration
DB_HOST=your-db-host.example.com
DB_PORT=3306
DB_USER=sargon_user
DB_PASSWORD=your_secure_password
DB_NAME=sargon_database

# Optional
DEFAULT_TENANT_ID=account-123
DB_QUERY_TIMEOUT_SECONDS=30
```

**Note:** Replace all example values with your actual credentials!

