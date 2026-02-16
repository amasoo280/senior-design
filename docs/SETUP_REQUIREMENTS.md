# Setup Requirements - What You Need to Run the Project

## Prerequisites

### System Requirements

1. **Python 3.9+**
   - Check: `python --version` or `python3 --version`
   - Download: https://www.python.org/downloads/

2. **Node.js 16+ and npm**
   - Check: `node --version` and `npm --version`
   - Download: https://nodejs.org/

3. **MySQL Database**
   - Access to Sargon Partners MySQL database
   - Database credentials (host, port, username, password, database name)

4. **AWS Account with Bedrock Access**
   - AWS Access Key ID
   - AWS Secret Access Key
   - AWS Region (e.g., us-east-1)
   - Bedrock model access enabled (Claude 3 Sonnet)

## Step-by-Step Setup

### 1. Backend Setup

#### Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

Or use a virtual environment (recommended):
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

#### Configure Environment Variables
```bash
# Copy the template
cp env.template .env

# Edit .env with your actual values:
```

**Required in `backend/.env`:**
```env
# AWS Credentials (REQUIRED)
AWS_ACCESS_KEY_ID=your_actual_aws_access_key
AWS_SECRET_ACCESS_KEY=your_actual_aws_secret_key
AWS_REGION=us-east-1

# Database Configuration (REQUIRED)
DB_HOST=your_database_host
DB_PORT=3306
DB_USER=your_database_username
DB_PASSWORD=your_database_password
DB_NAME=your_database_name
```

**Optional:**
```env
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
DEFAULT_TENANT_ID=your-tenant-id
DB_QUERY_TIMEOUT_SECONDS=30
```

#### Update Database Schema Context
**CRITICAL:** Edit `backend/app/schema/context.py` with your actual Sargon Partners database schema.

See `backend/SCHEMA_UPDATE.md` for detailed instructions.

#### Start Backend Server
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 2. Frontend Setup

#### Install Node Dependencies
```bash
cd frontend
npm install
```

#### Configure API URL (Optional)
Create `frontend/.env`:
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_DEFAULT_TENANT_ID=default
```

Or edit `frontend/src/config.ts` directly.

#### Start Frontend Dev Server
```bash
cd frontend
npm run dev
```

You should see:
```
  VITE v6.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### 3. Verify Setup

#### Test Backend
```bash
# Health check
curl http://localhost:8000/health

# Database connection test
curl http://localhost:8000/db-ping
```

#### Test Frontend
1. Open browser: `http://localhost:5173`
2. You should see the Sargon AI chat interface
3. Try asking a question like "What equipment is active?"

## Required Information Checklist

Before you can run the project, you need:

### AWS Credentials
- [ ] AWS Access Key ID
- [ ] AWS Secret Access Key
- [ ] AWS Region
- [ ] Bedrock access enabled in AWS account
- [ ] Claude 3 Sonnet model access granted

### Database Credentials
- [ ] Database host (IP or hostname)
- [ ] Database port (usually 3306 for MySQL)
- [ ] Database name
- [ ] Database username
- [ ] Database password
- [ ] Network access to database (firewall/VPN if needed)

### Database Schema Information
- [ ] Table names
- [ ] Column names and types
- [ ] Relationships between tables
- [ ] Tenant ID column name (for multi-tenancy)
- [ ] Sample data structure

## Common Issues & Solutions

### Backend Won't Start

**Error: "Missing required field: db_host"**
- Solution: Make sure `.env` file exists in `backend/` directory with all required fields

**Error: "No module named 'fastapi'"**
- Solution: Run `pip install -r requirements.txt` in the backend directory

**Error: "AWS credentials not found"**
- Solution: Add AWS credentials to `backend/.env` file

**Error: "Database connection failed"**
- Solution: Verify database credentials and network connectivity

### Frontend Won't Start

**Error: "'vite' is not recognized"**
- Solution: Run `npm install` in the frontend directory

**Error: "Cannot connect to backend"**
- Solution: 
  1. Make sure backend is running on port 8000
  2. Check `VITE_API_BASE_URL` in frontend config
  3. Check CORS settings in backend

### API Errors

**Error: "Bedrock API error: AccessDeniedException"**
- Solution: Verify Bedrock model access is enabled in AWS account

**Error: "SQL validation failed"**
- Solution: Check that generated SQL includes tenant_id filter

## Quick Start Commands

```bash
# Terminal 1 - Backend
cd backend
pip install -r requirements.txt
# Create .env file with credentials
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm install
npm run dev
```

## Next Steps After Setup

1. ✅ Update schema context with real database schema
2. ✅ Test with a simple query
3. ✅ Verify tenant isolation is working
4. ✅ Test error handling
5. ✅ Review generated SQL for accuracy

## Need Help?

- See `backend/TESTING.md` for testing instructions
- See `backend/SCHEMA_UPDATE.md` for schema configuration
- Check backend logs for detailed error messages
- Verify all environment variables are set correctly

