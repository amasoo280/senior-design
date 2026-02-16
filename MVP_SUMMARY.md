# MVP Summary: NL→SQL Query System

## 🎯 Goal
A working frontend that allows users to type natural language queries and receive responses from an LLM (AWS Bedrock). The system doesn't need to execute SQL against a real database or provide perfectly accurate responses—it just needs to work end-to-end.

---

## ✅ What's Already Built

### Backend (mostly complete)
| Component | Status | Location |
|-----------|--------|----------|
| FastAPI server setup | ✅ Done | `backend/main.py` |
| AWS Bedrock client | ✅ Done | `backend/app/bedrock/client.py` |
| SQL safety guardrails | ✅ Done | `backend/app/safety/guardrails.py` |
| Schema context module | ✅ Done | `backend/app/schema/context.py` |
| SQL executor (DB connection) | ✅ Done | `backend/app/executor/executor.py` |
| Config module | ✅ Done | `backend/app/config.py` |

### Frontend (UI complete, needs integration)
| Component | Status | Location |
|-----------|--------|----------|
| React + TypeScript + Vite setup | ✅ Done | `frontend/` |
| Dashboard UI | ✅ Done | `frontend/src/components/Dashboard.tsx` |
| Query input box | ✅ Done | Built into Dashboard |
| Results display | ✅ Done | Built into Dashboard |
| Loading states | ✅ Done | Built into Dashboard |

---

## 🚨 Critical Gaps for MVP

### 1. Backend: Create `/ask` Endpoint
**Owner:** _[Assign]_  
**Priority:** HIGH  
**Effort:** ~2-3 hours

The `main.py` currently only has a `/db-ping` endpoint. We need to create the `/ask` endpoint that:
- Accepts a natural language query + tenant_id
- Calls the Bedrock client to generate SQL
- Validates the SQL with guardrails
- Returns the generated SQL + explanation

**File to modify:** `backend/main.py`

**What it should look like:**
```python
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from app.bedrock.client import BedrockClient
from app.safety.guardrails import SQLGuardrails
from app.schema.context import SchemaContext

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str
    tenant_id: Optional[str] = "default"

class QueryResponse(BaseModel):
    sql: str
    explanation: str
    natural_language_query: str
    tenant_id: str
    validated: bool

@app.post("/ask", response_model=QueryResponse)
async def ask(
    request: QueryRequest,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
):
    tenant_id = x_tenant_id or request.tenant_id or "default"
    
    try:
        # Initialize components
        bedrock_client = BedrockClient()
        schema_context = SchemaContext()
        guardrails = SQLGuardrails(tenant_id)
        
        # Generate SQL from natural language
        result = bedrock_client.generate_sql(
            natural_language_query=request.query,
            schema_context=schema_context.get_schema_context(),
            tenant_id=tenant_id
        )
        
        # Validate the generated SQL
        is_valid, error_message = guardrails.validate_query(result["sql"])
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"SQL validation failed: {error_message}")
        
        return QueryResponse(
            sql=result["sql"],
            explanation=result["explanation"],
            natural_language_query=request.query,
            tenant_id=tenant_id,
            validated=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "healthy"}
```

---

### 2. Frontend: Connect to Backend API
**Owner:** _[Assign]_  
**Priority:** HIGH  
**Effort:** ~1-2 hours

The Dashboard currently uses mock data. Update it to call the real `/ask` endpoint.

**File to modify:** `frontend/src/components/Dashboard.tsx`

**Changes needed in `executeQuery` function (around line 39-75):**
```typescript
const executeQuery = async () => {
  if (!query.trim()) return;

  setIsLoading(true);
  
  try {
    const response = await fetch('http://localhost:8000/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        query: query,
        tenant_id: 'tenant-123'  // Can be hardcoded for MVP
      })
    });
    
    if (!response.ok) {
      throw new Error('API request failed');
    }
    
    const data = await response.json();
    
    // For MVP: Display the generated SQL as a result
    // (Real execution against DB can come later)
    const mockResult = {
      query: query,
      timestamp: new Date().toISOString(),
      data: [],  // Empty for now - no real DB execution
      summary: `Generated SQL: ${data.sql}`,
      sql: data.sql,
      explanation: data.explanation
    };
    
    setQueryResults(mockResult);
    setHistory(prev => [{ query, timestamp: new Date().toISOString() }, ...prev.slice(0, 9)]);
  } catch (err) {
    console.error('Query failed:', err);
    // TODO: Show error to user
  } finally {
    setIsLoading(false);
  }
};
```

---

### 3. AWS Credentials Setup
**Owner:** _[Assign]_  
**Priority:** HIGH  
**Effort:** ~30 mins

Set up AWS credentials with Bedrock access. The backend needs these environment variables:

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
```

**Requirements:**
- AWS account with Bedrock enabled in us-east-1
- IAM user/role with `bedrock:InvokeModel` permission
- Access to Claude 3 Sonnet model (`anthropic.claude-3-sonnet-20240229-v1:0`)

---

## 📋 MVP Task Checklist

| # | Task | Owner | Status |
|---|------|-------|--------|
| 1 | Create `/ask` endpoint in `main.py` | _TBD_ | ⬜ Not started |
| 2 | Update Dashboard to call real API | _TBD_ | ⬜ Not started |
| 3 | Get AWS credentials with Bedrock access | _TBD_ | ⬜ Not started |
| 4 | Test backend endpoint with Postman/curl | _TBD_ | ⬜ Not started |
| 5 | Test full flow: Frontend → Backend → Bedrock | _TBD_ | ⬜ Not started |

---

## 🚀 How to Test the MVP

### Step 1: Start Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Set AWS credentials
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-east-1

# Start server
uvicorn main:app --reload --port 8000
```

### Step 2: Test Backend Directly
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"query": "What equipment is active at Site A?", "tenant_id": "tenant-123"}'
```

Expected response:
```json
{
  "sql": "SELECT * FROM equipment WHERE status = 'Active' AND location = 'Site A' AND tenant_id = 'tenant-123'",
  "explanation": "...",
  "natural_language_query": "What equipment is active at Site A?",
  "tenant_id": "tenant-123",
  "validated": true
}
```

### Step 3: Start Frontend
```bash
cd frontend
npm install
npm run dev
```

### Step 4: Test Full Flow
1. Open http://localhost:5173
2. Type a query like "What equipment is active?"
3. Click "Submit Query"
4. Should see the generated SQL in the results

---

## ⚠️ What's NOT Needed for MVP

- ❌ User authentication
- ❌ Perfect SQL accuracy
- ❌ Logging/monitoring
- ❌ Rate limiting
- ❌ Production deployment

---

## 🗄️ OPTIONAL: Adding Database Connectivity

If you want the MVP to actually execute queries against a real database (not just generate SQL), here's what you need:

### What's Already Built
- ✅ SQL Executor module (`backend/app/executor/executor.py`)
- ✅ Database config module (`backend/app/config.py`)
- ✅ SQLAlchemy + PyMySQL in requirements

### Additional Tasks for DB Connectivity

| # | Task | Effort |
|---|------|--------|
| 6 | Set up MySQL database (local or RDS) | ~1-2 hours |
| 7 | Create tables matching the schema | ~30 mins |
| 8 | Add sample data for testing | ~30 mins |
| 9 | Update `/ask` endpoint to execute SQL | ~1 hour |
| 10 | Update frontend to display real results | ~1 hour |

---

### Task 6: Database Setup Options

**Option A: Local MySQL (easiest for development)**
```bash
# Using Docker
docker run --name mysql-dev -e MYSQL_ROOT_PASSWORD=password -e MYSQL_DATABASE=equipment_db -p 3306:3306 -d mysql:8

# Or install MySQL locally via Homebrew (Mac)
brew install mysql
brew services start mysql
```

**Option B: AWS RDS MySQL**
- Create RDS MySQL instance in AWS console
- Note the endpoint, username, password
- Ensure security group allows connections from your IP

**Option C: SQLite (simplest, no setup)**
Modify `backend/app/executor/executor.py` to use SQLite:
```python
DATABASE_URL = "sqlite:///./test.db"
```

---

### Task 7: Create Database Tables

Run this SQL to create the tables that match your schema context:

```sql
-- Create the equipment database
CREATE DATABASE IF NOT EXISTS equipment_db;
USE equipment_db;

-- Equipment table
CREATE TABLE equipment (
    id VARCHAR(50) PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    status VARCHAR(50) DEFAULT 'Available',
    days_active INT DEFAULT 0,
    deployed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tenant (tenant_id),
    INDEX idx_status (status),
    INDEX idx_location (location)
);

-- Jobs table
CREATE TABLE jobs (
    id VARCHAR(50) PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'Active',
    INDEX idx_tenant (tenant_id)
);

-- Equipment assignments table
CREATE TABLE equipment_assignments (
    equipment_id VARCHAR(50),
    job_id VARCHAR(50),
    tenant_id VARCHAR(50) NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (equipment_id, job_id),
    FOREIGN KEY (equipment_id) REFERENCES equipment(id),
    FOREIGN KEY (job_id) REFERENCES jobs(id),
    INDEX idx_tenant (tenant_id)
);
```

---

### Task 8: Add Sample Data

```sql
-- Sample equipment for tenant-123
INSERT INTO equipment (id, tenant_id, name, location, status, days_active) VALUES
('EQ-001', 'tenant-123', 'Excavator A', 'Site A', 'Active', 15),
('EQ-002', 'tenant-123', 'Crane B', 'Site A', 'Active', 22),
('EQ-003', 'tenant-123', 'Loader C', 'Site B', 'Maintenance', 0),
('EQ-004', 'tenant-123', 'Bulldozer D', 'Site A', 'Active', 45),
('EQ-005', 'tenant-123', 'Forklift E', 'Site C', 'Available', 0);

-- Sample jobs
INSERT INTO jobs (id, tenant_id, name, status) VALUES
('JOB-001', 'tenant-123', 'Highway Construction', 'Active'),
('JOB-002', 'tenant-123', 'Building Foundation', 'Active'),
('JOB-003', 'tenant-123', 'Demolition Project', 'Completed');

-- Sample assignments
INSERT INTO equipment_assignments (equipment_id, job_id, tenant_id) VALUES
('EQ-001', 'JOB-001', 'tenant-123'),
('EQ-002', 'JOB-001', 'tenant-123'),
('EQ-004', 'JOB-002', 'tenant-123');
```

---

### Task 9: Environment Variables for Database

Create `backend/.env` file:
```env
# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=password
DB_NAME=equipment_db

# AWS Configuration
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
```

---

### Task 10: Updated `/ask` Endpoint with Execution

Update `backend/main.py` to optionally execute queries:

```python
from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.bedrock.client import BedrockClient
from app.safety.guardrails import SQLGuardrails
from app.schema.context import SchemaContext
from app.executor.executor import execute_query, DatabaseExecutionError

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str
    tenant_id: Optional[str] = "default"
    execute: Optional[bool] = False  # Whether to execute the SQL

class QueryResponse(BaseModel):
    sql: str
    explanation: str
    natural_language_query: str
    tenant_id: str
    validated: bool
    results: Optional[List[Dict[str, Any]]] = None  # Query results if executed
    executed: bool = False

@app.post("/ask", response_model=QueryResponse)
async def ask(
    request: QueryRequest,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
):
    tenant_id = x_tenant_id or request.tenant_id or "default"
    
    try:
        # Initialize components
        bedrock_client = BedrockClient()
        schema_context = SchemaContext()
        guardrails = SQLGuardrails(tenant_id)
        
        # Generate SQL from natural language
        result = bedrock_client.generate_sql(
            natural_language_query=request.query,
            schema_context=schema_context.get_schema_context(),
            tenant_id=tenant_id
        )
        
        # Validate the generated SQL
        is_valid, error_message = guardrails.validate_query(result["sql"])
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"SQL validation failed: {error_message}")
        
        # Optionally execute the query
        query_results = None
        executed = False
        
        if request.execute:
            try:
                query_results = execute_query(result["sql"])
                executed = True
            except DatabaseExecutionError as e:
                raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        
        return QueryResponse(
            sql=result["sql"],
            explanation=result["explanation"],
            natural_language_query=request.query,
            tenant_id=tenant_id,
            validated=True,
            results=query_results,
            executed=executed
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/db-ping")
def db_ping():
    try:
        rows = execute_query("SELECT 1 AS ok;")
        return {"status": "ok", "result": rows}
    except DatabaseExecutionError as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}")
```

---

### Task 11: Updated Frontend to Display Real Results

Update the `executeQuery` function in `Dashboard.tsx`:

```typescript
const executeQuery = async () => {
  if (!query.trim()) return;

  setIsLoading(true);
  
  try {
    const response = await fetch('http://localhost:8000/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        query: query,
        tenant_id: 'tenant-123',
        execute: true  // Set to true to execute against DB
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'API request failed');
    }
    
    const data = await response.json();
    
    // Transform DB results to match Equipment interface
    const equipmentData = (data.results || []).map((row: any) => ({
      id: row.id,
      name: row.name,
      location: row.location,
      status: row.status,
      daysActive: row.days_active || 0
    }));
    
    setQueryResults({
      query: query,
      timestamp: new Date().toISOString(),
      data: equipmentData,
      summary: data.executed 
        ? `Found ${equipmentData.length} results. SQL: ${data.sql}`
        : `Generated SQL (not executed): ${data.sql}`
    });
    
    setHistory(prev => [{ query, timestamp: new Date().toISOString() }, ...prev.slice(0, 9)]);
  } catch (err: any) {
    console.error('Query failed:', err);
    alert(`Query failed: ${err.message}`);
  } finally {
    setIsLoading(false);
  }
};
```

---

### Updated Task Checklist (with DB)

| # | Task | Owner | Status |
|---|------|-------|--------|
| 1 | Create `/ask` endpoint in `main.py` | _TBD_ | ⬜ |
| 2 | Update Dashboard to call real API | _TBD_ | ⬜ |
| 3 | Get AWS credentials with Bedrock access | _TBD_ | ⬜ |
| 4 | Test backend endpoint with curl | _TBD_ | ⬜ |
| 5 | Test full flow (no DB) | _TBD_ | ⬜ |
| **6** | **Set up MySQL database** | _TBD_ | ⬜ |
| **7** | **Create tables** | _TBD_ | ⬜ |
| **8** | **Add sample data** | _TBD_ | ⬜ |
| **9** | **Update /ask to execute SQL** | _TBD_ | ⬜ |
| **10** | **Update frontend for real results** | _TBD_ | ⬜ |
| **11** | **Test full flow with DB** | _TBD_ | ⬜ |

### Timeline with Database
- **Without DB:** 1-2 days
- **With DB:** 2-3 days

---

## 📁 Key Files Reference

```
senior-design/
├── backend/
│   ├── main.py                    ← NEEDS WORK: Add /ask endpoint
│   ├── app/
│   │   ├── bedrock/client.py      ← Ready to use
│   │   ├── safety/guardrails.py   ← Ready to use
│   │   └── schema/context.py      ← Ready to use
│   └── requirements.txt
│
└── frontend/
    └── src/components/
        └── Dashboard.tsx          ← NEEDS WORK: Call real API
```

---

## 👥 Team Assignment Suggestions

| Person | Tasks |
|--------|-------|
| Backend Dev | Tasks 1, 4 (Create /ask endpoint, test it) |
| Frontend Dev | Task 2 (Connect Dashboard to API) |
| DevOps/Anyone | Task 3 (Get AWS credentials) |
| Everyone | Task 5 (Final integration testing) |

---

## 📅 Estimated Timeline

With focused effort, MVP can be completed in **1-2 days**:
- Day 1: Tasks 1-3 (Backend endpoint, AWS setup)
- Day 2: Tasks 2, 4-5 (Frontend integration, testing)

---

## ❓ Questions to Resolve

1. Who has access to create AWS credentials for Bedrock?
2. Should we use a shared AWS account or individual credentials?
3. What tenant_id should we use for testing?

---

*Generated: Dec 2, 2025*

