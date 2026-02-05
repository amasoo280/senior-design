# Sargon Partners AI Chatbot - Senior Design Project

An AI-powered chatbot that converts natural language queries to SQL and executes them against the Sargon Partners database using AWS Bedrock (Claude 3 Sonnet). Now with **Google OAuth 2.0** authentication and role-based access control.

## Architecture

```
senior-design/
├── backend/          # FastAPI backend with Bedrock integration
│   ├── app/
│   │   ├── bedrock/  # AWS Bedrock client
│   │   ├── executor/ # SQL executor (database connection)
│   │   ├── safety/   # SQL safety guardrails
│   │   ├── schema/   # Database schema context
│   │   ├── models.py # User database models
│   │   ├── database.py # Database connection & session
│   │   ├── auth.py   # JWT token & authentication
│   │   └── oauth.py  # Google OAuth integration
│   ├── main.py       # FastAPI server with OAuth endpoints
│   ├── init_db.py    # Database initialization script
│   └── .env          # Environment variables (create from env.template)
└── frontend/         # React + TypeScript frontend
    ├── src/
    │   ├── components/
    │   │   ├── Dashboard.tsx  # Main chatbot UI
    │   │   └── Login.tsx      # Google OAuth login
    │   ├── utils/auth.ts      # Authentication utilities
    │   └── config.ts          # API configuration
    └── package.json
```

## Features

- **Google OAuth 2.0 Authentication**: Secure login with Google accounts
- **Role-Based Access Control**: Admin vs standard user permissions  
- **Natural Language to SQL**: Converts questions to SQL using AWS Bedrock
- **Database Integration**: Executes queries against Sargon Partners MySQL database
- **Tenant Isolation**: Enforces multi-tenant security with tenant_id filtering
- **SQL Safety**: Validates queries to prevent data modification and SQL injection
- **Modern UI**: React-based dashboard with real-time query results
- **JWT Tokens**: Secure session management with JSON Web Tokens

## Quick Start

### Prerequisites

1. **Google OAuth Credentials**: Follow [OAUTH_SETUP.md](OAUTH_SETUP.md) to set up Google OAuth
2. **AWS Bedrock Access**: AWS account with Bedrock API access
3. **MySQL Database**: Access to Sargon Partners database
4. **Python** 3.8+ and **Node.js** 18+

### Backend Setup

1. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp env.template .env
   # Edit .env with ALL required credentials:
   # - AWS credentials and Bedrock settings
   # - Database credentials  
   # - Google OAuth Client ID and Secret (from OAUTH_SETUP.md)
   # - JWT Secret Key (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
   # - Admin emails (optional)
   ```

3. **Initialize database**:
   ```bash
   python init_db.py
   ```
   This creates the `users` table in your MySQL database.

4. **Update schema context** (important!):
   - Edit `backend/app/schema/context.py` with your actual database schema
   - Or use the `update_schema()` method to load from a file

5. **Start server**:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with:
   # - VITE_GOOGLE_CLIENT_ID (same as backend GOOGLE_CLIENT_ID)
   # - VITE_API_BASE_URL=http://localhost:8000 (default)
   # - VITE_DEFAULT_TENANT_ID (your tenant ID)
   ```

3. **Start dev server**:
   ```bash
   npm run dev
   ```

4. **Open browser**: Navigate to `http://localhost:5173`
   - Click "Sign in with Google"
   - Complete Google authentication
   - You'll be redirected to the dashboard

### First Time Login

1. Visit `http://localhost:5173`
2. Click **"Sign in with Google"**
3. Select your Google account
4. Grant permissions
5. You'll be logged in and see the chatbot dashboard

To make yourself an admin:
- **Option 1**: Add your email to `ADMIN_EMAILS` in backend `.env` before first login
- **Option 2**: Manually update the database:
  ```sql
  UPDATE users SET role='admin' WHERE email='your-email@example.com';
  ```

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
