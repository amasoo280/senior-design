# Senior Design Project - NL→SQL Query System

A full-stack application for converting natural language queries to SQL using AWS Bedrock, with a React frontend and FastAPI backend.

## Project Structure

```
.
├── backend/              # FastAPI backend server
│   ├── app/             # Application modules
│   │   ├── bedrock/     # AWS Bedrock client for NL→SQL
│   │   ├── safety/      # SQL safety guardrails
│   │   ├── schema/      # Database schema context
│   │   └── executor/    # SQL executor (to be implemented)
│   ├── main.py          # FastAPI application entry point
│   ├── requirements.txt # Python dependencies
│   └── README.md        # Backend documentation
│
├── frontend/            # React + TypeScript frontend
│   ├── src/            # Source code
│   │   ├── components/ # React components
│   │   ├── App.tsx     # Root component
│   │   └── main.tsx    # Application entry point
│   ├── index.html      # HTML template
│   ├── package.json    # Node.js dependencies
│   ├── vite.config.ts  # Vite configuration
│   ├── tailwind.config.js  # Tailwind CSS configuration
│   └── tsconfig.json   # TypeScript configuration
│
├── .vscode/            # VS Code settings (optional)
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## Features

### Backend
- **NL→SQL Generation**: Converts natural language to SQL using AWS Bedrock (Claude 3 Sonnet)
- **Tenant Isolation**: Enforces multi-tenant security with automatic tenant_id filtering
- **SQL Safety**: Validates queries to prevent dangerous operations and SQL injection
- **Schema Context**: Provides database schema information for accurate SQL generation

### Frontend
- **Natural Language Interface**: User-friendly query input with autocomplete suggestions
- **Real-time Results**: Interactive query results with equipment cards and status indicators
- **Query History**: Tracks recent queries for easy reference
- **Responsive Design**: Modern UI that works on desktop and mobile devices

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **AWS Bedrock** - Generative AI for NL→SQL conversion
- **boto3** - AWS SDK for Python
- **Pydantic** - Data validation

### Frontend
- **React 18** with TypeScript
- **Tailwind CSS** - Utility-first CSS framework
- **Vite** - Fast build tool and dev server
- **Lucide React** - Icon library

## Getting Started

### Prerequisites

- **Node.js** (version 16 or higher) - for frontend
- **Python** (version 3.9 or higher) - for backend
- **npm** or **yarn** - for frontend dependencies
- **AWS Account** with Bedrock access - for NL→SQL generation

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure AWS credentials:
   ```bash
   # Option 1: Environment variables
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_REGION=us-east-1
   
   # Option 2: AWS credentials file (~/.aws/credentials)
   ```

5. Start the backend server:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

The backend API will be available at:
- **API**: `http://localhost:8000`
- **Docs**: `http://localhost:8000/docs` (Swagger UI)
- **Health**: `http://localhost:8000/health`

For detailed backend documentation, see [backend/README.md](backend/README.md).

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:5173`

### Available Scripts (Frontend)

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Development Workflow

### Running Both Servers

1. **Terminal 1 - Backend**:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. **Terminal 2 - Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

### API Integration

The frontend is configured to call the backend `/ask` endpoint. Ensure the backend is running on port 8000 before using the frontend.

**API Endpoint**: `POST http://localhost:8000/ask`

**Request Body**:
```json
{
  "query": "What equipment is active at Site A?",
  "tenant_id": "tenant-123"
}
```

## Project Status

✅ **Completed**:
- Backend module structure
- Bedrock client for NL→SQL generation
- SQL safety guardrails
- Schema context module
- `/ask` API endpoint
- Frontend UI components

🔄 **In Progress**:
- RDS executor module
- Frontend-backend integration

📋 **Planned**:
- Database connection and query execution
- Authentication and authorization
- Rate limiting and caching
- Monitoring and logging

For detailed roadmap, see [backend/ROADMAP.md](backend/ROADMAP.md).

## Environment Variables

### Backend

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key | Required |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | Required |
| `AWS_REGION` | AWS region | `us-east-1` |
| `BEDROCK_MODEL_ID` | Bedrock model ID | `anthropic.claude-3-sonnet-20240229-v1:0` |
| `DEFAULT_TENANT_ID` | Default tenant ID | `default` |

### Frontend

Frontend environment variables can be configured in `.env` files:
- `.env` - Default environment variables
- `.env.local` - Local overrides (gitignored)

Example:
```env
VITE_API_URL=http://localhost:8000
```

## Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

This project is for demonstration purposes.
