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

1. **Google OAuth Credentials**: Follow [OAUTH_SETUP.md](docs/OAUTH_SETUP.md) to set up Google OAuth
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
   # - Google OAuth Client ID and Secret (from docs/OAUTH_SETUP.md)
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

```env
# AWS Bedrock
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Database
DB_HOST=your_database_host
DB_PORT=3306
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password

# Google OAuth
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret

# JWT
JWT_SECRET_KEY=your_secure_random_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Frontend
FRONTEND_URL=http://localhost:5173

# Admin (optional)
ADMIN_EMAILS=admin@example.com

# Other
DEFAULT_TENANT_ID=your_tenant_id
```

### Frontend (.env)

```env
VITE_GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
VITE_API_BASE_URL=http://localhost:8000
VITE_DEFAULT_TENANT_ID=your_tenant_id
```

## API Endpoints

### Authentication

- `POST /auth/google` - Exchange Google OAuth token for JWT
- `GET /auth/me` - Get current user information
- `POST /auth/logout` - Logout (server-side logging)
- `GET /auth/verify` - Verify JWT token validity

### Chatbot

- `POST /ask` - Send a natural language query (requires authentication)
  - Request: `{ "question": "Show me all equipment" }`
  - Response: `{ "answer": "...", "sql": "...", "data": [...] }`

### System

- `GET /health` - Health check endpoint
- `GET /db-ping` - Test database connectivity
- `GET /logs` - View request logs (requires authentication)
- `GET /analytics` - View usage analytics (requires authentication)

## How It Works

1. **User Authentication**: Users sign in with Google OAuth
2. **Backend Verification**: Backend verifies Google token and creates JWT
3. **Natural Language Input**: User asks a question in plain English
4. **AI Processing**: Claude 3 Sonnet converts the question to SQL
5. **SQL Validation**: Safety guardrails check the SQL query
6. **Database Execution**: Safe queries are executed against MySQL
7. **Response**: Results are returned and displayed in the UI

## Security Features

- **OAuth 2.0**: Industry-standard authentication with Google
- **JWT Tokens**: Stateless, secure session management
- **SQL Injection Prevention**: Parameterized queries and validation
- **Read-Only Queries**: Only SELECT statements allowed
- **Tenant Isolation**: Automatic tenant_id filtering
- **Role-Based Access**: Admin and user roles for future features
- **CORS Protection**: Restricted to allowed origins

## Project Structure

```
backend/
├── app/
│   ├── bedrock/         # AWS Bedrock integration
│   │   └── client.py    # Bedrock client wrapper
│   ├── executor/        # SQL execution
│   │   └── executor.py  # Database query executor
│   ├── safety/          # Security validation
│   │   └── validator.py # SQL safety checks
│   ├── schema/          # Database schema
│   │   └── context.py   # Schema context for AI
│   ├── models.py        # User database models
│   ├── database.py      # Database connection
│   ├── auth.py          # JWT authentication
│   ├── oauth.py         # Google OAuth
│   └── config.py        # Configuration management
├── main.py              # FastAPI application
├── init_db.py           # Database initialization
├── requirements.txt     # Python dependencies
└── env.template         # Environment template

frontend/
├── src/
│   ├── components/
│   │   ├── Dashboard.tsx    # Main UI
│   │   ├── Login.tsx        # OAuth login
│   │   ├── ChatInterface.tsx
│   │   ├── Analytics.tsx
│   │   └── Logs.tsx
│   ├── utils/
│   │   └── auth.ts          # Auth utilities
│   ├── config.ts            # API config
│   ├── App.tsx              # Main app
│   └── main.tsx             # Entry point
├── package.json
└── vite.config.ts
```

## Documentation

- **[OAUTH_SETUP.md](docs/OAUTH_SETUP.md)** - Complete guide to setting up Google OAuth
- **[RUNNING_THE_APP.md](docs/RUNNING_THE_APP.md)** - Step-by-step running instructions
- **[START_HERE.md](START_HERE.md)** - Original setup guide (pre-OAuth)

## Future Enhancements

- [ ] Per-account database isolation
- [ ] Enhanced SQL validation
- [ ] Query result visualization (charts/graphs)
- [ ] Admin dashboard for user management
- [ ] Configurable prompts and guardrails
- [ ] Example/suggested questions
- [ ] User feedback collection

## License

This is a senior design project for educational purposes.

## Contributors

Senior Design Team - Sargon Partners AI Chatbot
