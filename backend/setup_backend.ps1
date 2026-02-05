<# 
    setup_backend.ps1
    ------------------
    Backend setup script for Senior Design (SargonPartners).

    What it does:
    - Ensures you're in the backend folder
    - Creates a virtual environment (./venv) if it doesn't exist
    - Activates the venv
    - Upgrades pip
    - Installs dependencies (requirements.txt + SQLAlchemy, PyMySQL, etc.)
#>

Write-Host "=== Senior Design Backend Setup ===" -ForegroundColor Cyan

# 1. Move to the directory where this script lives (backend/)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir
Write-Host "Working directory: $(Get-Location)"

# 2. Check or create virtual environment
$venvPath = Join-Path $scriptDir "venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"

if (-Not (Test-Path $venvPython)) {
    Write-Host "No virtual environment found. Creating venv at: $venvPath" -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to create virtual environment. Make sure Python is installed and on PATH." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Virtual environment already exists at: $venvPath" -ForegroundColor Green
}

# 3. Activate venv for this script
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& "$venvPath\Scripts\Activate.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to activate virtual environment." -ForegroundColor Red
    Write-Host "If you see an execution policy error, run PowerShell as Administrator and execute:" -ForegroundColor Yellow
    Write-Host "  Set-ExecutionPolicy RemoteSigned" -ForegroundColor Yellow
    exit 1
}

# 4. Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip

# 5. Install dependencies from requirements.txt (if it exists)
if (Test-Path "requirements.txt") {
    Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Cyan
    pip install -r requirements.txt
} else {
    Write-Host "requirements.txt not found, skipping that step." -ForegroundColor Yellow
}

# 6. Ensure core backend deps are installed
Write-Host "Installing core backend packages (FastAPI, Uvicorn, SQLAlchemy, PyMySQL, python-dotenv)..." -ForegroundColor Cyan
pip install fastapi "uvicorn[standard]" sqlalchemy pymysql python-dotenv

Write-Host ""
Write-Host "=== Backend setup complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1) In VS Code / Cursor, select the interpreter:" -ForegroundColor Gray
Write-Host "   Python: Select Interpreter -> $venvPython" -ForegroundColor Gray
Write-Host "2) Run the backend with:" -ForegroundColor Gray
Write-Host "   uvicorn main:app --reload" -ForegroundColor Gray
Write-Host ""
