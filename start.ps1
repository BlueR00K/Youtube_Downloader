# YouTube Downloader Project Launcher
Write-Host "Starting YouTube Downloader..." -ForegroundColor Green

# Function to check if a port is in use
function Test-PortInUse {
    param($port)
    $inUse = $false
    $listener = $null
    try {
        $listener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, $port)
        $listener.Start()
    }
    catch {
        $inUse = $true
    }
    finally {
        if ($listener) {
            $listener.Stop()
        }
    }
    return $inUse
}

# Kill any processes using our ports if they exist
$ports = @(8002, 5173)
foreach ($port in $ports) {
    if (Test-PortInUse $port) {
        Write-Host "Port $port is in use. Attempting to free it..." -ForegroundColor Yellow
        $processId = (Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue).OwningProcess
        if ($processId) {
            Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
        }
    }
}

# Set working directory to script location
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptPath

# Create and activate virtual environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Install backend dependencies
Write-Host "Installing backend dependencies..." -ForegroundColor Yellow
pip install -r webapp\backend\requirements.txt

# Install frontend dependencies
Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
Set-Location webapp\frontend
if (-not (Test-Path "node_modules")) {
    npm install
}

# Start backend in a new window
Write-Host "Starting backend server..." -ForegroundColor Green
$backendPath = Join-Path $scriptPath "webapp\backend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$backendPath'; & ..\..\\.venv\Scripts\Activate.ps1; uvicorn app.main:app --host 127.0.0.1 --port 8002"

# Start frontend in a new window
Write-Host "Starting frontend development server..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$scriptPath\webapp\frontend'; npm run dev"

Write-Host "`nYouTube Downloader is starting up!`n" -ForegroundColor Cyan
Write-Host "Frontend will be available at: http://localhost:5173" -ForegroundColor White
Write-Host "Backend API will be available at: http://localhost:8002" -ForegroundColor White
Write-Host "`nClose this window and the server windows when you're done.`n" -ForegroundColor Yellow