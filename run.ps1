# Barekat Startup Helper Script
# This script stops any running instances of the services first, then starts them fresh.
# It automatically prefers Docker Compose if Docker is active; otherwise, it runs them locally.

$DockerActive = $false
try {
    # Check if Docker daemon is running
    docker info > $null 2>&1
    if ($LASTEXITCODE -eq 0) {
        $DockerActive = $true
    }
} catch {
    $DockerActive = $false
}

Write-Host "=========================================" -ForegroundColor Green
Write-Host "   Barekat Platform Startup Manager      " -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green

# ----------------- STOPPING SERVICES FIRST -----------------
Write-Host "Stopping any running services..." -ForegroundColor Yellow

# 1. Stop Docker Compose containers if running
if ($DockerActive) {
    Write-Host "Stopping Docker containers..." -ForegroundColor Yellow
    docker compose down > $null 2>&1
}

# 2. Stop local processes on ports 8000 and 5173
$PortsToKill = @(8000, 5173)
foreach ($Port in $PortsToKill) {
    try {
        $Connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        if ($Connections) {
            foreach ($Conn in $Connections) {
                $PidToKill = $Conn.OwningProcess
                if ($PidToKill -gt 0) {
                    Write-Host "Stopping local process ID $PidToKill using port $Port..." -ForegroundColor Yellow
                    Stop-Process -Id $PidToKill -Force -ErrorAction SilentlyContinue
                }
            }
        }
    } catch {
        # Ignore errors
    }
}

Write-Host "All services stopped successfully." -ForegroundColor Green
Write-Host "-----------------------------------------" -ForegroundColor Green
# -----------------------------------------------------------

if ($DockerActive) {
    Write-Host "[Docker Mode] Docker is active. Running stack via Docker Compose..." -ForegroundColor Cyan
    
    Write-Host "Starting Barekat containers..." -ForegroundColor Yellow
    docker compose up -d
    Write-Host "Running database migrations..." -ForegroundColor Yellow
    docker compose exec backend python manage.py migrate
    
    Write-Host "`nAll services are up!" -ForegroundColor Green
    Write-Host "Frontend: http://localhost:5173/" -ForegroundColor Cyan
    Write-Host "Backend API: http://localhost:8000/api/" -ForegroundColor Cyan
} else {
    Write-Host "[Local Mode] Docker daemon is not active. Running services natively..." -ForegroundColor Yellow
    
    # --- Start Backend (Port 8000) ---
    Write-Host "Starting Backend in a new window..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "
        Set-Location '$PSScriptRoot\backend';
        Write-Host 'Setting up Backend Virtual Environment...' -ForegroundColor Cyan;
        if (-not (Test-Path venv)) {
            python -m venv venv
        }
        . \venv\Scripts\Activate;
        Write-Host 'Installing dependencies...' -ForegroundColor Cyan;
        pip install -r requirements.txt;
        
        Write-Host 'Checking database migrations...' -ForegroundColor Cyan;
        python manage.py migrate;
        
        Write-Host 'Starting Django server on http://127.0.0.1:8000/' -ForegroundColor Green;
        python manage.py runserver;
    "

    # --- Start Frontend (Port 5173) ---
    Write-Host "Starting Frontend in a new window..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "
        Set-Location '$PSScriptRoot\frontend';
        Write-Host 'Installing Node dependencies...' -ForegroundColor Cyan;
        npm install;
        Write-Host 'Starting React Vite dev server on http://localhost:5173/' -ForegroundColor Green;
        npm run dev;
    "
    
    Write-Host "`nLocal servers have been triggered!" -ForegroundColor Green
    Write-Host "Frontend: http://localhost:5173/" -ForegroundColor Cyan
    Write-Host "Backend API: http://localhost:8000/api/" -ForegroundColor Cyan
}

Write-Host "=========================================" -ForegroundColor Green
Write-Host "Press any key to exit this script..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
