# NL→SQL Backend Roadmap

## ✅ Completed

- [x] Backend module structure (`backend/app/`)
- [x] Bedrock client for NL→SQL generation
- [x] SQL safety guardrails with tenant isolation
- [x] Schema context module with default equipment schema
- [x] `/ask` endpoint with Bedrock integration
- [x] Prompt templates for NL→SQL conversion
- [x] Requirements.txt with dependencies
- [x] FastAPI server setup with CORS

## 🔄 In Progress

- [ ] Testing the `/ask` endpoint with AWS Bedrock
- [ ] Verifying SQL safety guardrails

## 📋 Next Steps

### Phase 1: RDS Integration (High Priority)

#### 1.1 SQL Executor Module
- [ ] Create `backend/app/executor/executor.py`
- [ ] Implement PostgreSQL/MySQL connection pool
- [ ] Add connection configuration (environment variables)
- [ ] Implement `execute_query()` method
- [ ] Add query timeout handling
- [ ] Implement result formatting (JSON)
- [ ] Add connection retry logic
- [ ] Handle connection errors gracefully

#### 1.2 Update `/ask` Endpoint
- [ ] Add optional `execute` parameter to `/ask` endpoint
- [ ] Integrate executor with `/ask` endpoint
- [ ] Return query results along with SQL
- [ ] Add pagination support for large results
- [ ] Implement query result caching

#### 1.3 Database Configuration
- [ ] Create database connection configuration module
- [ ] Support multiple database types (PostgreSQL, MySQL)
- [ ] Add connection pool configuration
- [ ] Implement database health checks

### Phase 2: Frontend Integration (Medium Priority)

#### 2.1 Frontend API Integration
- [ ] Update `src/components/Dashboard.tsx` to call `/ask` endpoint
- [ ] Replace mock data with real API calls
- [ ] Add error handling for API failures
- [ ] Update request format to match backend
- [ ] Add tenant ID configuration (from context/auth)

#### 2.2 UI Enhancements
- [ ] Add loading states for Bedrock API calls
- [ ] Display generated SQL alongside results
- [ ] Show SQL explanation in UI
- [ ] Add error messages for validation failures
- [ ] Display Bedrock API errors gracefully

#### 2.3 Query Options
- [ ] Add toggle to show/hide generated SQL
- [ ] Add option to execute query or just generate SQL
- [ ] Add query history persistence (localStorage or API)

### Phase 3: Security & Performance (Medium Priority)

#### 3.1 Authentication & Authorization
- [ ] Implement JWT token authentication
- [ ] Add tenant ID extraction from JWT claims
- [ ] Add role-based access control (RBAC)
- [ ] Validate tenant ID against user permissions

#### 3.2 Rate Limiting
- [ ] Add rate limiting per tenant
- [ ] Add rate limiting per user/IP
- [ ] Configure rate limit thresholds
- [ ] Return proper rate limit headers

#### 3.3 Caching
- [ ] Implement query result caching (Redis)
- [ ] Cache frequently used schema contexts
- [ ] Add cache invalidation logic
- [ ] Configure cache TTL per query type

### Phase 4: Monitoring & Logging (Low Priority)

#### 4.1 Logging
- [ ] Add structured logging (JSON logs)
- [ ] Log all SQL queries generated
- [ ] Log Bedrock API calls and costs
- [ ] Log query execution times
- [ ] Add log rotation

#### 4.2 Monitoring
- [ ] Add health check endpoint with database status
- [ ] Add metrics endpoint (Prometheus)
- [ ] Track Bedrock API usage and costs
- [ ] Monitor query execution performance
- [ ] Add alerting for errors

#### 4.3 Analytics
- [ ] Track most common queries per tenant
- [ ] Analyze query generation accuracy
- [ ] Track safety validation failures
- [ ] Generate usage reports

### Phase 5: Advanced Features (Future)

#### 5.1 Schema Management
- [ ] Dynamic schema discovery from database
- [ ] Schema versioning
- [ ] Schema updates via API
- [ ] Multi-schema support (different schemas per tenant)

#### 5.2 Query Optimization
- [ ] Add query explanation before execution
- [ ] Suggest query optimizations
- [ ] Add query plan analysis
- [ ] Implement query complexity scoring

#### 5.3 Advanced SQL Features
- [ ] Support for JOINs across tables
- [ ] Support for aggregations (COUNT, SUM, AVG, etc.)
- [ ] Support for subqueries
- [ ] Support for window functions
- [ ] Support for CTEs (Common Table Expressions)

#### 5.4 User Experience
- [ ] Query history with re-execution
- [ ] Save favorite queries
- [ ] Export query results (CSV, JSON)
- [ ] Query templates for common questions
- [ ] Natural language query suggestions

## 🔧 Technical Debt & Improvements

### Code Quality
- [ ] Add unit tests for all modules
- [ ] Add integration tests for `/ask` endpoint
- [ ] Add E2E tests for full flow
- [ ] Improve error messages and validation
- [ ] Add type hints everywhere
- [ ] Add docstrings for all functions

### Documentation
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Deployment guide
- [ ] Architecture diagrams
- [ ] Database schema documentation
- [ ] Troubleshooting guide

### Configuration
- [ ] Move all configuration to environment variables
- [ ] Create `.env.example` file
- [ ] Add configuration validation on startup
- [ ] Support configuration files (YAML/TOML)

## 🚀 Deployment Considerations

### Infrastructure
- [ ] Dockerize the application
- [ ] Create `Dockerfile` and `docker-compose.yml`
- [ ] Set up CI/CD pipeline
- [ ] Configure production environment variables
- [ ] Set up database migrations (Alembic)

### AWS Integration
- [ ] Configure AWS credentials securely (IAM roles)
- [ ] Set up VPC for RDS access
- [ ] Configure Bedrock model access
- [ ] Set up CloudWatch logging
- [ ] Configure auto-scaling

### Security Hardening
- [ ] Enable HTTPS/TLS
- [ ] Restrict CORS origins in production
- [ ] Add input sanitization
- [ ] Implement SQL query sanitization
- [ ] Add request size limits
- [ ] Configure security headers

## 📊 Success Metrics

- [ ] Query generation accuracy > 90%
- [ ] API response time < 2 seconds
- [ ] Safety validation failure rate < 1%
- [ ] Query execution success rate > 95%
- [ ] System uptime > 99.9%

## 🎯 Immediate Next Steps (Priority Order)

1. **Test `/ask` endpoint** with AWS Bedrock credentials
2. **Create SQL executor** to connect to RDS database
3. **Update `/ask` endpoint** to optionally execute queries
4. **Frontend integration** - connect React to `/ask` endpoint
5. **Add error handling** and user-friendly error messages
6. **Test full flow** - NL query → SQL → execution → results

## 📝 Notes

- Frontend integration should wait until backend is fully functional
- RDS executor is the critical missing piece for end-to-end functionality
- Testing with real AWS Bedrock credentials is essential before proceeding
- Consider adding a "dry-run" mode for SQL generation without execution



