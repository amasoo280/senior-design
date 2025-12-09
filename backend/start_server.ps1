# Backend Server Startup Script
Write-Host "Starting Sargon AI Backend Server..." -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "❌ ERROR: .env file not found!" -ForegroundColor Red
    Write-Host "   Please copy env.template to .env and fill in your credentials" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ .env file found" -ForegroundColor Green

# Check if config can load
Write-Host "Testing configuration..." -ForegroundColor Cyan
try {
    python -c "from app.config import settings; print('✅ Config loaded successfully')" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Config loading failed. Check .env file." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Error loading config: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting server on http://localhost:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Start the server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

