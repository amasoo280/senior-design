@echo off
echo Starting Sargon AI Backend Server...
echo.

REM Check if .env exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Please copy env.template to .env and fill in your credentials
    pause
    exit /b 1
)

echo .env file found
echo.

REM Test config
echo Testing configuration...
python -c "from app.config import settings; print('Config OK')" 2>nul
if errorlevel 1 (
    echo ERROR: Config loading failed. Check .env file.
    pause
    exit /b 1
)

echo.
echo Starting server on http://localhost:8000
echo Press Ctrl+C to stop
echo.

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause

