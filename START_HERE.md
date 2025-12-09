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

## Step 3: Test

1. **Test backend:** Open `http://localhost:8000/health` in browser
2. **Test frontend:** Open `http://localhost:5173` in browser
3. **Try a query:** Ask "Show me all equipment locations"

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

