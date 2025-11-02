<#
One-click launcher for the Youtube_Downloader project (Windows PowerShell).

Behavior:
- If Docker is available, runs docker compose build && docker compose up in a new window.
- Otherwise, creates/uses a Python venv for the backend and starts uvicorn in a new window,
  then starts the frontend dev server (Vite) in another window and opens the browser.

Usage:
- Double-click this file in Explorer, or run from PowerShell with:
    powershell -ExecutionPolicy Bypass -File .\run_all.ps1

Notes:
- You may be prompted to allow running scripts. If so, run PowerShell as Administrator and:
    Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
#>

Set-StrictMode -Version Latest

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Write-Host "Repository root: $RepoRoot"

function Start-DockerCompose {
    param($Path)
    $cmd = "cd '$Path'; .\scripts\up.ps1 -Build"
    Start-Process -FilePath pwsh -ArgumentList @('-NoExit', '-Command', $cmd) -WindowStyle Normal
}

function Start-Backend-Dev {
    param($Path)
    $backend = Join-Path $Path 'webapp\backend'

    $setup = @(
        "cd '$backend'",
        "if(-not (Test-Path '.\\.venv')) { python -m venv .\\.venv; .\\.venv\\Scripts\\Activate.ps1; pip install -r requirements.txt }",
        ".\\.venv\\Scripts\\Activate.ps1",
        "uvicorn app.main:app --reload --host 0.0.0.0 --port 8001"
    ) -join '; '

    Start-Process -FilePath powershell -ArgumentList @('-NoExit', '-Command', $setup) -WindowStyle Normal
}

function Start-Frontend-Dev {
    param($Path)
    $frontend = Join-Path $Path 'webapp\frontend'

    $setup = @(
        "cd '$frontend'",
        "if(-not (Test-Path 'node_modules')) { npm install }",
        "npm run dev"
    ) -join '; '

    Start-Process -FilePath powershell -ArgumentList @('-NoExit', '-Command', $setup) -WindowStyle Normal
}

# Entry
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "Docker detected - launching docker-compose (build + up)..."
    Start-DockerCompose -Path $RepoRoot
    Start-Sleep -Seconds 2
    Write-Host "If you prefer non-Docker dev mode, run this script again after closing the Docker window."
}
else {
    Write-Host "Docker not detected. Launching backend and frontend in separate windows..."
    Start-Backend-Dev -Path $RepoRoot
    Start-Sleep -Seconds 1
    Start-Frontend-Dev -Path $RepoRoot
    Start-Sleep -Seconds 2
    # open frontend URL
    try {
        Start-Process 'http://localhost:5173'
    }
    catch {
        Write-Host "Open your browser and navigate to http://localhost:5173"
    }
}

Write-Host "Done. Check the new terminal windows for server logs."
<#
One-click launcher for the Youtube_Downloader project (Windows PowerShell).

Behavior:
- If Docker is available, runs docker compose build && docker compose up in a new window.
- Otherwise, creates/uses a Python venv for the backend and starts uvicorn in a new window,
  then starts the frontend dev server (Vite) in another window and opens the browser.

Usage:
- Double-click this file in Explorer, or run from PowerShell with:
    powershell -ExecutionPolicy Bypass -File .\run_all.ps1

Notes:
- You may be prompted to allow running scripts. If so, run PowerShell as Administrator and:
    Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
#>

Set-StrictMode -Version Latest

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Write-Host "Repository root: $RepoRoot"

function Start-DockerCompose {
    param($Path)
    $cmd = "cd '$Path'; .\scripts\up.ps1 -Build"
    Start-Process -FilePath pwsh -ArgumentList @('-NoExit', '-Command', $cmd) -WindowStyle Normal
}

function Start-Backend-Dev {
    param($Path)
    $backend = Join-Path $Path 'webapp\backend'

    $setup = @(
        "cd '$backend'",
        "if(-not (Test-Path '.\\.venv')) { python -m venv .\\.venv; .\\.venv\\Scripts\\Activate.ps1; pip install -r requirements.txt }",
        ".\\.venv\\Scripts\\Activate.ps1",
        "uvicorn app.main:app --reload --host 0.0.0.0 --port 8001"
    ) -join '; '

    Start-Process -FilePath powershell -ArgumentList @('-NoExit', '-Command', $setup) -WindowStyle Normal
}

function Start-Frontend-Dev {
    param($Path)
    $frontend = Join-Path $Path 'webapp\frontend'

    $setup = @(
        "cd '$frontend'",
        "if(-not (Test-Path 'node_modules')) { npm install }",
        "npm run dev"
    ) -join '; '

    Start-Process -FilePath powershell -ArgumentList @('-NoExit', '-Command', $setup) -WindowStyle Normal
}

# Entry
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "Docker detected - launching docker-compose (build + up)..."
    Start-DockerCompose -Path $RepoRoot
    Start-Sleep -Seconds 2
    Write-Host "If you prefer non-Docker dev mode, run this script again after closing the Docker window."
}
else {
    Write-Host "Docker not detected. Launching backend and frontend in separate windows..."
    Start-Backend-Dev -Path $RepoRoot
    Start-Sleep -Seconds 1
    Start-Frontend-Dev -Path $RepoRoot
    Start-Sleep -Seconds 2
    # open frontend URL
    try {
        Start-Process 'http://localhost:5173'
    }
    catch {
        Write-Host "Open your browser and navigate to http://localhost:5173"
    }
}

Write-Host "Done. Check the new terminal windows for server logs."
<#
One-click launcher for the Youtube_Downloader project (Windows PowerShell).

Behavior:
- If Docker is available, runs docker compose build && docker compose up in a new window.
- Otherwise, creates/uses a Python venv for the backend and starts uvicorn in a new window,
  then starts the frontend dev server (Vite) in another window and opens the browser.

Usage:
- Double-click this file in Explorer, or run from PowerShell with:
    powershell -ExecutionPolicy Bypass -File .\run_all.ps1

Notes:
- You may be prompted to allow running scripts. If so, run PowerShell as Administrator and:
    Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
#>

Set-StrictMode -Version Latest

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Write-Host "Repository root: $RepoRoot"

function Start-DockerCompose {
    param($Path)
    $cmd = "cd '$Path'; .\scripts\up.ps1 -Build"
    Start-Process -FilePath pwsh -ArgumentList @('-NoExit', '-Command', $cmd) -WindowStyle Normal
}

function Start-Backend-Dev {
    param($Path)
    $backend = Join-Path $Path 'webapp\backend'

    $setup = @(
        "cd '$backend'",
        "if(-not (Test-Path '.\.venv')) { python -m venv .\.venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt }",
        ".\.venv\Scripts\Activate.ps1",
        "uvicorn app.main:app --reload --host 0.0.0.0 --port 8001"
    ) -join '; '

    Start-Process -FilePath powershell -ArgumentList @('-NoExit', '-Command', $setup) -WindowStyle Normal
}

function Start-Frontend-Dev {
    param($Path)
    $frontend = Join-Path $Path 'webapp\frontend'

    $setup = @(
        "cd '$frontend'",
        "if(-not (Test-Path 'node_modules')) { npm install }",
        "npm run dev"
    ) -join '; '

    Start-Process -FilePath powershell -ArgumentList @('-NoExit', '-Command', $setup) -WindowStyle Normal
}

# Entry
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "Docker detected — launching docker-compose (build + up)..."
    Start-DockerCompose -Path $RepoRoot
    Start-Sleep -Seconds 2
    Write-Host "If you prefer non-Docker dev mode, run this script again after closing the Docker window."
}
else {
    Write-Host "Docker not detected. Launching backend and frontend in separate windows..."
    Start-Backend-Dev -Path $RepoRoot
    Start-Sleep -Seconds 1
    Start-Frontend-Dev -Path $RepoRoot
    Start-Sleep -Seconds 2
    # open frontend URL
    try {
        Start-Process 'http://localhost:5173'
    }
    catch {
        Write-Host "Open your browser and navigate to http://localhost:5173"
    }
}

Write-Host "Done. Check the new terminal windows for server logs."
