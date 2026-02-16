# Quick Start Guide

## Step 1: Start Backend

**Option A - Using the startup script (Easiest):**
```powershell
cd backend
.\start_server.ps1
```

**Option B - Manual start:**
```powershell
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**What to look for:**
- Should see: `INFO: Uvicorn running on http://0.0.0.0:8000`
- If you see errors, check:
  - `.env` file exists in `backend/` directory
  - All required fields in `.env` are filled
  - Python dependencies installed (`pip install -r requirements.txt`)

## Step 2: Start Frontend

**In a NEW terminal window:**
```powershell
cd frontend
npm run dev
```

**What to look for:**
- Should see: `Local: http://localhost:5173/`
- Open that URL in your browser

## Step 3: Verify Everything Works

### Test Backend Health
Open in browser or use curl:
```powershell
# Health check
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# Database connection test
curl http://localhost:8000/db-ping
# Expected: {"status":"ok","result":[{"ok":1}]}
```

### Test Frontend
1. Open browser: `http://localhost:5173`
2. You should see the Sargon AI chat interface

### Test a Query
Try asking:
- "Show me all equipment locations"
- "What jobs are currently active?"
- "List all tags"
- "Show me employees"

## Common Issues

### Backend won't start
- Make sure `.env` file exists in `backend/` directory
- Check all required fields are filled (AWS credentials, DB credentials)
- Run: `pip install -r requirements.txt`

### "Failed to fetch" in frontend
- Make sure backend is running (check terminal)
- Verify backend is on port 8000
- Check browser console (F12) for detailed errors

### Port already in use
- Kill process on port 8000: `netstat -ano | findstr :8000`
- Or use different port: `--port 8001`

### Database connection fails
- Verify database credentials in `.env`
- Check network connectivity to database
- Ensure database is accessible from your machine

### API returns errors
- Check backend terminal for error messages
- Verify AWS credentials are correct
- Ensure Bedrock access is enabled
- Verify tenant_id is set (see `ENV_FILE_GUIDE.md`)

## Next Steps

Once everything is working:
1. Test with real queries from your database
2. Verify tenant isolation is working (accountId filtering)
3. Test error handling with invalid queries
4. Check that SQL generation is accurate

## Additional Documentation

- **Setup & Requirements:** See `SETUP_REQUIREMENTS.md`
- **Environment Variables:** See `ENV_FILE_GUIDE.md`
- **Troubleshooting:** See `TROUBLESHOOTING.md`
- **Backend Details:** See `backend/README.md`
- **Testing Guide:** See `backend/TESTING.md`

