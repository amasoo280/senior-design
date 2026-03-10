# NL→SQL FastAPI Backend

FastAPI server for converting natural language queries to SQL using AWS Bedrock with tenant isolation and safety guardrails.

## Architecture

```
backend/
├── main.py                 # FastAPI server with /ask endpoint
├── app/
│   ├── bedrock/           # AWS Bedrock client for NL→SQL generation
│   │   ├── __init__.py
│   │   └── client.py
│   ├── safety/            # SQL safety guardrails
│   │   ├── __init__.py
│   │   └── guardrails.py
│   ├── schema/            # Database schema context
│   │   ├── __init__.py
│   │   └── context.py
│   └── executor/          # SQL executor (RDS integration - TODO)
│       └── __init__.py
└── requirements.txt
```

## Features

- **NL→SQL Generation**: Converts natural language queries to SQL using AWS Bedrock (Claude 3 Sonnet)
- **Tenant Isolation**: Enforces tenant_id filtering in all queries for multi-tenant security
- **SQL Safety**: Validates generated SQL to prevent:
  - Data modification (INSERT, UPDATE, DELETE, etc.)
  - SQL injection attacks
  - Dangerous operations (DROP, ALTER, etc.)
- **Schema Context**: Provides database schema information to improve SQL generation accuracy

## Prerequisites

- Python 3.9+
- AWS Account with Bedrock access
- AWS Credentials configured (see Setup below)

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure AWS Credentials**

   Option A: Environment Variables
   ```bash
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_REGION=us-east-1
   ```

   Option B: AWS Credentials File (`~/.aws/credentials`)
   ```ini
   [default]
   aws_access_key_id = your_access_key
   aws_secret_access_key = your_secret_key
   region = us-east-1
   ```

3. **Configure Bedrock Model** (optional)
   ```bash
   export BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
   ```

4. **Set Default Tenant ID** (optional)
   ```bash
   export DEFAULT_TENANT_ID=your_tenant_id
   ```

## Running the Server

```bash
# Development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production server
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs` (Swagger UI)
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### POST /ask

Convert natural language query to SQL.

**Request Body:**
```json
{
  "query": "What equipment is active at Site A?",
  "tenant_id": "tenant-123"  // Optional, can use X-Tenant-ID header instead
}
```

**Headers (optional):**
```
X-Tenant-ID: tenant-123
```

**Response:**
```json
{
  "sql": "SELECT * FROM equipment WHERE status = 'Active' AND location = 'Site A' AND tenant_id = 'tenant-123'",
  "explanation": "Returns all active equipment at Site A for the specified tenant",
  "natural_language_query": "What equipment is active at Site A?",
  "tenant_id": "tenant-123",
  "validated": true
}
```

**Error Responses:**
- `400`: Invalid request or SQL failed safety validation
- `503`: AWS Bedrock service error
- `500`: Internal server error

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

### GET /

Root endpoint with API information.

## Usage Examples

### Using cURL

```bash
# Basic request
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me all equipment at Site A",
    "tenant_id": "tenant-123"
  }'

# Using header for tenant ID
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant-123" \
  -d '{
    "query": "What equipment has been active for more than 30 days?"
  }'
```

### Using Python

```python
import requests

response = requests.post(
    "http://localhost:8000/ask",
    json={
        "query": "What equipment is active at Site A?",
        "tenant_id": "tenant-123"
    }
)

result = response.json()
print(f"Generated SQL: {result['sql']}")
print(f"Explanation: {result['explanation']}")
```

## Safety Features

The SQL safety guardrails ensure:

1. **Read-Only Queries**: Only SELECT queries are allowed
2. **Keyword Blocking**: Blocks dangerous SQL keywords (INSERT, UPDATE, DELETE, DROP, etc.)
3. **SQL Injection Prevention**: Detects common SQL injection patterns
4. **Tenant Isolation**: All queries must include `tenant_id` filtering

## Customization

### Updating Schema Context

Modify `app/schema/context.py` to match your database schema:

```python
schema_context = SchemaContext({
    "description": "Your database description",
    "tables": [
        {
            "name": "your_table",
            "columns": [...]
        }
    ]
})
```

### Configuring Bedrock Model

Change the default model in `app/bedrock/client.py` or set `BEDROCK_MODEL_ID` environment variable.

### Adjusting Safety Rules

Modify validation rules in `app/safety/guardrails.py` to customize SQL safety checks.

## Next Steps

- [ ] Implement RDS executor in `app/executor/` to execute generated SQL
- [ ] Add query result caching
- [ ] Implement query history/logging
- [ ] Add rate limiting
- [ ] Set up proper CORS origins for production
- [ ] Add authentication/authorization

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key | Required |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | Required |
| `AWS_REGION` | AWS region | `us-east-1` |
| `BEDROCK_MODEL_ID` | Bedrock model ID | `anthropic.claude-3-sonnet-20240229-v1:0` |
| `DEFAULT_TENANT_ID` | Default tenant ID | `default` |

## License

This project is for demonstration purposes.

