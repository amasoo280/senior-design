from fastapi import FastAPI

app = FastAPI(title="Test Backend")


@app.get("/")
def root():
    return {"status": "ok", "message": "Hello from FastAPI"}
