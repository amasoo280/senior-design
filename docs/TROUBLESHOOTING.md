# Troubleshooting "Failed to fetch" Error

## Common Causes

### 1. Backend Not Running
**Symptom:** "Failed to fetch" in browser console

**Solution:**
```bash
# Check if backend is running
curl http://localhost:8000/health

# If not running, start it:
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Backend Crashed on Startup
**Symptom:** Backend starts then immediately stops

**Check:**
- Look at backend terminal for error messages
- Common issues:
  - Missing `.env` file
  - Invalid credentials in `.env`
  - Database connection failed
  - Missing Python dependencies

**Solution:**
```bash
# Check for errors
cd backend
python -c "from app.config import settings; print('Config OK')"

# If config fails, check .env file exists
# Make sure all required fields are filled
```

### 3. Wrong Port or URL
**Symptom:** Frontend can't connect

**Check:**
- Frontend config: `frontend/src/config.ts`
- Should be: `http://localhost:8000`
- Backend should be on port 8000

**Solution:**
```bash
# Verify backend is on port 8000
netstat -ano | findstr :8000

# Check frontend config
cat frontend/src/config.ts
```

### 4. CORS Issues
**Symptom:** CORS error in browser console

**Check:**
- Backend CORS settings in `backend/main.py`
- Frontend URL matches allowed origins

**Solution:**
- CORS is already configured for `http://localhost:5173`
- If using different port, update `backend/main.py` CORS settings

### 5. Firewall/Network Issues
**Symptom:** Connection timeout

**Solution:**
- Check Windows Firewall isn't blocking port 8000
- Try accessing `http://localhost:8000/health` directly in browser

## Quick Diagnostic Steps

1. **Test Backend Directly:**
   ```bash
   curl http://localhost:8000/health
   ```
   Should return: `{"status":"healthy"}`

2. **Check Backend Logs:**
   - Look at the terminal where backend is running
   - Check for Python errors or import errors

3. **Verify .env File:**
   ```bash
   cd backend
   # Make sure .env exists
   Test-Path .env
   
   # Check it has required fields (don't show values!)
   Get-Content .env | Select-String "DB_HOST|AWS_ACCESS"
   ```

4. **Test Database Connection:**
   ```bash
   curl http://localhost:8000/db-ping
   ```
   This will fail if database credentials are wrong

5. **Check Browser Console:**
   - Open browser DevTools (F12)
   - Go to Console tab
   - Look for detailed error messages
   - Check Network tab to see if request is being sent

## Step-by-Step Fix

1. **Stop all servers** (Ctrl+C in terminals)

2. **Verify .env file:**
   ```bash
   cd backend
   # Make sure .env exists and has all fields
   ```

3. **Test config loading:**
   ```bash
   cd backend
   python -c "from app.config import settings; print('OK')"
   ```

4. **Start backend:**
   ```bash
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   Watch for errors in the terminal

5. **Test backend:**
   ```bash
   curl http://localhost:8000/health
   ```

6. **Start frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

7. **Open browser:**
   - Go to `http://localhost:5173`
   - Check browser console (F12) for errors

## Common Error Messages

### "Missing required field: db_host"
- **Fix:** Add all required fields to `backend/.env`

### "No module named 'fastapi'"
- **Fix:** Run `pip install -r requirements.txt` in backend directory

### "Database connection failed"
- **Fix:** Check database credentials in `.env`
- Verify database is accessible from your machine

### "Bedrock API error"
- **Fix:** Check AWS credentials in `.env`
- Verify Bedrock access is enabled

### Port already in use
- **Fix:** Kill process using port 8000 or use different port

