# Testing Guide for MVP AI Chatbot

This guide explains how to test the end-to-end flow of the AI chatbot that queries the Sargon Partners database.

## Prerequisites

1. **Environment Variables**: Copy `env.template` to `.env` and fill in all required values:
   - AWS credentials (Bedrock access)
   - Database connection details
   - Optional: Default tenant ID

2. **Dependencies Installed**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Database Access**: Ensure you can connect to the Sargon Partners database with the provided credentials.

## Step 1: Update Schema Context

Before testing, update the schema context with your actual database structure:

1. Open `backend/app/schema/context.py`
2. Either:
   - Modify the `_get_default_schema()` method with your real schema, OR
   - Use `update_schema()` method to load schema from a file/API

The schema should include:
- Table names
- Column names and types
- Relationships between tables
- Important notes about query patterns

## Step 2: Start the Backend Server

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will be available at `http://localhost:8000`

## Step 3: Test Database Connection

```bash
curl http://localhost:8000/db-ping
```

Expected response:
```json
{
  "status": "ok",
  "result": [{"ok": 1}]
}
```

## Step 4: Test Health Endpoint

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy"
}
```

## Step 5: Test the `/ask` Endpoint

### Basic Test (Generate SQL Only)

```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: your-tenant-id" \
  -d '{
    "query": "What equipment is active at Site A?",
    "tenant_id": "your-tenant-id",
    "execute": false
  }'
```

### Full Test (Generate and Execute SQL)

```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: your-tenant-id" \
  -d '{
    "query": "Show me all equipment at Site A",
    "tenant_id": "your-tenant-id",
    "execute": true
  }'
```

Expected response structure:
```json
{
  "sql": "SELECT * FROM equipment WHERE location = 'Site A' AND tenant_id = 'your-tenant-id'",
  "explanation": "Returns all equipment at Site A for the specified tenant",
  "natural_language_query": "Show me all equipment at Site A",
  "tenant_id": "your-tenant-id",
  "validated": true,
  "rows": [...],
  "row_count": 5,
  "execution_error": null
}
```

## Step 6: Start the Frontend

In a new terminal:

```bash
cd frontend
npm install  # if not already done
npm run dev
```

The frontend will be available at `http://localhost:5173` (or the port Vite assigns).

## Step 7: Test End-to-End Flow

1. Open the frontend in your browser
2. Enter a natural language query (e.g., "What equipment is active?")
3. Click "Submit Query"
4. Verify:
   - Loading state appears
   - SQL is generated (click "Show Generated SQL")
   - Results are displayed in a table
   - Explanation is shown

## Troubleshooting

### AWS Bedrock Errors

- **Error 403**: Check AWS credentials and Bedrock model access
- **Error 503**: Verify AWS region and model ID
- **Timeout**: Check network connectivity to AWS

### Database Connection Errors

- Verify database credentials in `.env`
- Check database host/port accessibility
- Ensure database user has SELECT permissions
- Test connection with: `curl http://localhost:8000/db-ping`

### SQL Validation Errors

- Check that generated SQL includes `tenant_id` filter
- Verify SQL doesn't contain dangerous keywords
- Review guardrails in `app/safety/guardrails.py`

### Frontend Connection Issues

- Verify backend is running on port 8000
- Check CORS settings in `backend/main.py`
- Verify `VITE_API_BASE_URL` in frontend config (defaults to `http://localhost:8000`)

## Example Test Queries

Try these natural language queries:

1. "What equipment is active at Site A?"
2. "Show me all equipment deployed to Job X"
3. "Which assets have been operating for more than 30 days?"
4. "List equipment by location"
5. "What is the status of equipment ID 12345?"

## Next Steps

After basic testing works:

1. Update schema context with real Sargon Partners schema
2. Test with actual tenant IDs from your database
3. Verify tenant isolation is working correctly
4. Test edge cases (empty results, complex queries, etc.)
5. Add authentication/authorization if needed


