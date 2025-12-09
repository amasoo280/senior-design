# Quick Test Guide

## Servers Started

✅ Backend server starting on: `http://localhost:8000`  
✅ Frontend server starting on: `http://localhost:5173`

## Step 1: Verify Backend is Running

Open a new terminal and run:

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test database connection
curl http://localhost:8000/db-ping
```

**Expected responses:**
- Health: `{"status":"healthy"}`
- DB Ping: `{"status":"ok","result":[{"ok":1}]}`

## Step 2: Test the API Endpoint

Test the `/ask` endpoint with a simple query:

```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: your-account-id" \
  -d '{
    "query": "Show me all equipment locations",
    "tenant_id": "your-account-id",
    "execute": true
  }'
```

Replace `your-account-id` with an actual accountId from your database.

## Step 3: Open Frontend

1. Open your browser
2. Navigate to: `http://localhost:5173`
3. You should see the Sargon AI chat interface

## Step 4: Test a Query

Try asking:
- "Show me all equipment locations"
- "What jobs are currently active?"
- "List all tags"
- "Show me employees"

## Troubleshooting

### Backend won't start
- Check that `.env` file exists in `backend/` directory
- Verify all required fields are filled in
- Check for Python errors in the terminal

### Database connection fails
- Verify database credentials in `.env`
- Check network connectivity to database
- Ensure database is accessible from your machine

### Frontend won't connect
- Make sure backend is running on port 8000
- Check browser console for errors
- Verify CORS is configured correctly

### API returns errors
- Check backend terminal for error messages
- Verify AWS credentials are correct
- Ensure Bedrock access is enabled

## Next Steps

Once everything is working:
1. Test with real queries from your database
2. Verify tenant isolation is working (accountId filtering)
3. Test error handling with invalid queries
4. Check that SQL generation is accurate

