# Barekat Public Tunnel Exposer
# This script starts secure public tunnels for local Django and React servers.

Write-Host "=========================================" -ForegroundColor Green
Write-Host "   Barekat Exposer - Localtunnel Stack   " -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green

# ----------------- STOPPING EXISTING FRONTEND DEV SERVER -----------------
Write-Host "Checking for existing local frontend server on port 5173..." -ForegroundColor Yellow
try {
    $Connections = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue
    if ($Connections) {
        foreach ($Conn in $Connections) {
            $PidToKill = $Conn.OwningProcess
            if ($PidToKill -gt 0) {
                Write-Host "Stopping local frontend process ID $PidToKill..." -ForegroundColor Yellow
                Stop-Process -Id $PidToKill -Force -ErrorAction SilentlyContinue
            }
        }
    }
} catch {
    # Ignore errors
}

# ----------------- START BACKEND TUNNEL -----------------
Write-Host "`nStep 1: Starting Backend Tunnel..." -ForegroundColor Cyan
Write-Host "A new PowerShell window will open to run the backend tunnel." -ForegroundColor Gray
Start-Process powershell -ArgumentList "-NoExit", "-Command", "
    Write-Host '=========================================' -ForegroundColor Cyan;
    Write-Host '     Django API Public Tunnel (Port 8000) ' -ForegroundColor Cyan;
    Write-Host '=========================================' -ForegroundColor Cyan;
    Write-Host 'Launching localtunnel. If asked to install, press Y and Enter.' -ForegroundColor Yellow;
    npx localtunnel --port 8000;
"

# Prompt the user for the backend URL
Write-Host ""
Write-Host "Please wait for the backend tunnel window to display the URL." -ForegroundColor Yellow
Write-Host "Example format: https://xxxx.loca.lt" -ForegroundColor Gray
$BackendUrl = Read-Host "Enter the complete backend URL (including https://)"
$BackendUrl = $BackendUrl.Trim()

if (-not $BackendUrl.StartsWith("http")) {
    Write-Host "Invalid URL format. Exiting." -ForegroundColor Red
    Exit
}

# Remove trailing slash if any
if ($BackendUrl.EndsWith("/")) {
    $BackendUrl = $BackendUrl.Substring(0, $BackendUrl.Length - 1)
}

$env:VITE_API_URL = "$BackendUrl/api/"
Write-Host "`nBackend API URL set to: $env:VITE_API_URL" -ForegroundColor Green

# ----------------- START FRONTEND SERVER WITH ENV -----------------
Write-Host "`nStep 2: Building and serving production Frontend with public API URL..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "
    Set-Location '$PSScriptRoot\frontend';
    Write-Host '=========================================' -ForegroundColor Green;
    Write-Host '        React Frontend Production Server' -ForegroundColor Green;
    Write-Host '=========================================' -ForegroundColor Green;
    Write-Host 'Injected API URL: $env:VITE_API_URL' -ForegroundColor Cyan;
    `$env:VITE_API_URL = '$env:VITE_API_URL';
    Write-Host 'Building application assets...' -ForegroundColor Yellow;
    npm run build;
    Write-Host 'Serving static files on port 5173...' -ForegroundColor Green;
    npx serve -s dist -l 5173;
"

# ----------------- START FRONTEND TUNNEL -----------------
Write-Host "`nStep 3: Starting Frontend Tunnel..." -ForegroundColor Cyan
Write-Host "A new PowerShell window will open to run the frontend tunnel." -ForegroundColor Gray
Start-Process powershell -ArgumentList "-NoExit", "-Command", "
    Write-Host '=========================================' -ForegroundColor Magenta;
    Write-Host '      Vite App Public Tunnel (Port 5173) ' -ForegroundColor Magenta;
    Write-Host '=========================================' -ForegroundColor Magenta;
    npx localtunnel --port 5173;
"

Write-Host "`n=========================================" -ForegroundColor Green
Write-Host " Tunnels launched successfully!" -ForegroundColor Green
Write-Host " 1. Use the URL from the Frontend tunnel window to open the app on any device." -ForegroundColor Cyan
Write-Host " 2. Keep this and all other tunnel windows open." -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Green
