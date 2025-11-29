from fastapi import FastAPI, HTTPException
from app.executor.executor import execute_query, DatabaseExecutionError

app = FastAPI()

@app.get("/db-ping")
def db_ping():
    try:
        rows = execute_query("SELECT 1 AS ok;")
        return {"status": "ok", "result": rows}
    except DatabaseExecutionError as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}")
