# Sargon Partners AI Chatbot - Senior Design Project

An AI-powered chatbot that converts natural language queries to SQL and executes them against the Sargon Partners database using AWS Bedrock (Claude 3 Sonnet).

## Architecture

```
senior-design/
├── backend/          # FastAPI backend with Bedrock integration
│   ├── app/
│   │   ├── bedrock/  # AWS Bedrock client
│   │   ├── executor/ # SQL executor (database connection)
│   │   ├── safety/   # SQL safety guardrails
│   │   └── schema/   # Database schema context
│   ├── main.py       # FastAPI server with /ask endpoint
│   └── .env          # Environment variables (create from env.template)
└── frontend/         # React + TypeScript frontend
    ├── src/
    │   ├── components/
    │   │   └── Dashboard.tsx  # Main chatbot UI
    │   └── config.ts           # API configuration
    └── package.json
```

## Features

- **Natural Language to SQL**: Converts questions to SQL using AWS Bedrock
- **Database Integration**: Executes queries against Sargon Partners MySQL database
- **Tenant Isolation**: Enforces multi-tenant security with tenant_id filtering
- **SQL Safety**: Validates queries to prevent data modification and SQL injection
- **Modern UI**: React-based dashboard with real-time query results

## Quick Start

### Backend Setup

1. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp env.template .env
   # Edit .env with your AWS credentials and database details
   ```

3. **Update schema context** (important!):
   - Edit `backend/app/schema/context.py` with your actual database schema
   - Or use the `update_schema()` method to load from a file

4. **Start server**:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Configure API URL** (optional):
   - Create `.env` file with `VITE_API_BASE_URL=http://localhost:8000`
   - Or edit `src/config.ts` directly

3. **Start dev server**:
   ```bash
   npm run dev
   ```

4. **Open browser**: Navigate to `http://localhost:5173`

## Environment Variables

### Backend (.env)

Required:
- `AWS_ACCESS_KEY_ID` - AWS access key for Bedrock
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_REGION` - AWS region (e.g., us-east-1)
- `DB_HOST` - Database hostname/IP
- `DB_PORT` - Database port (default: 3306)
- `DB_NAME` - Database name
- `DB_USER` - Database username
- `DB_PASSWORD` - Database password

Optional:
- `BEDROCK_MODEL_ID` - Bedrock model (default: Claude 3 Sonnet)
- `DEFAULT_TENANT_ID` - Default tenant ID for testing
- `DB_QUERY_TIMEOUT_SECONDS` - Query timeout (default: 30)

### Frontend (.env)

Optional:
- `VITE_API_BASE_URL` - Backend API URL (default: http://localhost:8000)
- `VITE_DEFAULT_TENANT_ID` - Default tenant ID (default: "default")

## API Endpoints

### POST /ask

Convert natural language to SQL and optionally execute it.

**Request:**
```json
{
  "query": "What equipment is active at Site A?",
  "tenant_id": "tenant-123",
  "execute": true
}
```

**Response:**
```json
{
  "sql": "SELECT * FROM equipment WHERE status = 'Active' AND location = 'Site A' AND tenant_id = 'tenant-123'",
  "explanation": "Returns all active equipment at Site A",
  "natural_language_query": "What equipment is active at Site A?",
  "tenant_id": "tenant-123",
  "validated": true,
  "rows": [...],
  "row_count": 5,
  "execution_error": null
}
```

### GET /health

Health check endpoint.

### GET /db-ping

Test database connection.

## Testing

See [backend/TESTING.md](backend/TESTING.md) for detailed testing instructions.

## Project Status

### ✅ Completed
- Backend API with Bedrock integration
- SQL executor with database connection
- Safety guardrails and tenant isolation
- Frontend UI with API integration
- Error handling and logging

### 🔄 Next Steps
- Update schema context with real Sargon Partners schema
- Add authentication/authorization
- Improve error messages and UX
- Add query history persistence
- Performance optimization

## Documentation

- [Backend README](backend/README.md) - Detailed backend documentation
- [Backend Roadmap](backend/ROADMAP.md) - Feature roadmap
- [Testing Guide](backend/TESTING.md) - Testing instructions

## License

This project is for demonstration purposes.
