param(
  [switch]$Build
)

Set-Location -Path "$PSScriptRoot/.."

if ($Build) {
  Write-Host "Building docker images..."
  docker compose build
}

Write-Host "Starting services (attached). Use Ctrl+C to stop."
docker compose up
