# Sargon Partners AI Chatbot — Senior Design Project

An AI-powered chatbot that converts natural language questions into SQL and executes them against the Invisi-Tag equipment tracking database. Built on AWS Bedrock (Claude), Auth0, and a React + FastAPI stack.

---

## Architecture

```
senior-design/
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── auth.py           # Auth0 JWT validation
│   │   ├── config.py         # Settings & environment variables
│   │   ├── bedrock/          # AWS Bedrock client (NL→SQL, prompt caching)
│   │   ├── executor/         # SQL query executor (MySQL)
│   │   ├── safety/           # SQL guardrails & tenant isolation
│   │   ├── schema/           # Database schema context sent to the model
│   │   ├── history/          # Chat session & conversation persistence
│   │   ├── metrics/          # Token usage & request tracking
│   │   └── logging/          # Structured request logging
│   ├── main.py               # FastAPI application & all endpoints
│   └── requirements.txt
└── frontend/                 # React + TypeScript frontend
    └── src/
        ├── components/
        │   ├── Dashboard.tsx       # Main chat UI
        │   ├── AdminDashboard.tsx  # Admin panel
        │   └── LogsViewer.tsx      # Request logs viewer
        ├── utils/auth.ts           # Auth0 token helpers
        └── config.ts               # API endpoint config
```

---

## Features

- **Auth0 Authentication** — Secure login; tenant ID is linked to the Auth0 account
- **Natural Language to SQL** — Claude converts plain English questions into SQL queries
- **Streaming Responses** — Real-time SSE streaming of model output to the frontend
- **Prompt Caching** — Static system prompt and schema are cached with AWS Bedrock, reducing input token costs by ~98% per session
- **Token Usage Tracking** — Every request logs input tokens, output tokens, cache reads, and cache writes
- **Session-Based Chat History** — Conversations are persisted per session and restored on page refresh, including result tables and charts
- **Bar & Pie Chart Generation** — Model detects chart requests and returns rendered visualisations
- **SQL Safety Guardrails** — Only SELECT queries allowed; automatic tenant isolation; SQL injection pattern blocking
- **Multi-Tenant Support** — All queries are scoped to the authenticated user's `accountId`
- **Admin Dashboard** — View analytics, configure the LLM prompt template, set database context notes, manage sample questions, and view per-tenant metrics and logs

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- AWS account with Bedrock access (Claude model enabled)
- Auth0 tenant with an API and application configured
- MySQL access to the Invisi-Tag database

---

### Backend Setup

1. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Create `.env`** (see [Environment Variables](#environment-variables) below)

3. **Start the server**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   On first start, the server automatically creates the `chat_sessions` and `conversations` tables in your database if they don't exist.

---

### Frontend Setup

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Create `.env`** (see [Environment Variables](#environment-variables) below)

3. **Start the dev server**
   ```bash
   npm run dev
   ```

4. Open `http://localhost:5173` in your browser

---

## Environment Variables

### Backend — `backend/.env`

```env
# AWS Bedrock
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0

# Database (Invisi-Tag MySQL)
DB_HOST=your_database_host
DB_PORT=3306
DB_NAME=invistagmysql
DB_USER=your_database_user
DB_PASSWORD=your_database_password

# Auth0
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_AUDIENCE=https://your-api-identifier

# Admin access (comma-separated emails)
ADMIN_EMAILS=admin@example.com

# Tenant
DEFAULT_TENANT_ID=your_tenant_uuid
ALLOWED_TENANT_IDS=uuid1,uuid2   # optional; DEFAULT_TENANT_ID is always allowed

# Chart rendering
CHART_SERVICE_BASE_URL=https://quickchart.io/chart
```

### Frontend — `frontend/.env`

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_AUTH0_DOMAIN=your-tenant.auth0.com
VITE_AUTH0_CLIENT_ID=your_auth0_client_id
VITE_AUTH0_AUDIENCE=https://your-api-identifier
VITE_DEFAULT_TENANT_ID=your_tenant_uuid
```

---

## API Endpoints

### Chat

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/ask` | NL query — batch (returns full response) |
| `POST` | `/ask/stream` | NL query — streaming SSE (used by frontend) |

### Sessions & History

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/sessions` | List chat sessions for the current user |
| `POST` | `/sessions` | Create a new chat session |
| `DELETE` | `/sessions/{id}` | Delete a session and its messages |
| `PUT` | `/sessions/{id}/title` | Rename a session |
| `GET` | `/history` | Get all messages for a session |
| `POST` | `/history` | Save a conversation turn |

### Admin

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/analytics` | Aggregate usage metrics |
| `GET/POST` | `/admin/config/prompt` | Get / update the LLM prompt template and DB context |
| `GET/POST` | `/admin/config/llm` | Get / update LLM settings (max tokens, etc.) |
| `GET` | `/admin/config/guardrails` | View current guardrail configuration |
| `GET` | `/admin/metrics/{tenant_id}` | Per-tenant request metrics |
| `GET` | `/admin/logs` | Recent structured request logs |
| `GET` | `/admin/tenant-ids` | List all known tenant IDs |

### System

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/auth/me` | Current authenticated user info |
| `GET` | `/health` | Health check |
| `GET` | `/db-ping` | Test database connectivity |
| `GET` | `/logs` | Request logs (authenticated users) |

---

## How It Works

1. **Login** — User authenticates via Auth0. The tenant ID is linked to their Auth0 account and included in every request.
2. **Question** — User types a natural language question (e.g. *"Show me all active assets at the warehouse"*).
3. **Prompt Construction** — The backend assembles a prompt with static system instructions and the full Invisi-Tag database schema, marked for caching.
4. **Bedrock Request** — The prompt is sent to AWS Bedrock (Claude). On the first request of a session the static portions are cached; subsequent requests in the same session pay ~10% of normal input token cost for cached content.
5. **SQL Generation** — Claude returns a structured JSON response with `mode` (`sql`, `chat`, or `clarification`) and a SQL query if applicable.
6. **Guardrails** — The SQL is validated: only SELECT statements are permitted, the query must filter by the user's `accountId`, and common injection patterns are blocked.
7. **Execution** — The validated SQL is run against the Invisi-Tag MySQL database.
8. **Response** — Results are streamed back to the frontend. If the user asked for a chart, a rendered bar or pie chart is included.
9. **Persistence** — The conversation turn (query, response, SQL, result rows, chart data) is saved to the `conversations` table and restored on next page load.

---

## Security

- **Auth0 JWT** — Every API request requires a valid Bearer token issued by Auth0
- **Tenant Isolation** — All SQL queries automatically include `WHERE accountId = '<tenant>'`; the model is instructed never to omit this filter
- **Read-Only Enforcement** — Only `SELECT` statements are permitted; any `INSERT`, `UPDATE`, `DELETE`, `DROP`, etc. is rejected before execution
- **SQL Injection Blocking** — Common injection patterns are matched and blocked by the guardrails layer
- **Admin Role** — Admin-only endpoints require the requesting user's email to appear in `ADMIN_EMAILS`
- **Sensitive Column Exclusion** — UUIDs, passwords, PINs, and auth tokens are excluded from the schema context so the model never references or returns them

---

## Token Cost Optimisation

The system prompt and database schema are static on every request. By marking these blocks with `cache_control` in the Bedrock request, they are cached server-side for 5 minutes and subsequent requests within that window are billed at approximately 10% of the normal input token rate.

In testing, a simple query that cost **1,479 input tokens** on the first request cost only **28 input tokens** on subsequent requests — a ~98% reduction.

> **Note:** AWS Bedrock does not currently support prompt caching and extended thinking on the same request. The streaming endpoint (used by the frontend) currently uses extended thinking for higher-quality SQL generation; caching can be re-enabled by removing the thinking configuration if cost reduction is the priority.

---

## Contributors

Senior Design Team — Sargon Partners AI Chatbot
