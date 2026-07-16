$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker Desktop is required: https://www.docker.com/products/docker-desktop/"
}
docker info *> $null
if ($LASTEXITCODE -ne 0) { throw "Docker Desktop is not running" }
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }
docker compose up --build -d
if ($LASTEXITCODE -ne 0) { throw "docker compose up failed" }
$deadline = (Get-Date).AddMinutes(4)
do {
    try {
        $catalog = Invoke-RestMethod -TimeoutSec 5 "http://127.0.0.1:3000/api-backend/products?limit=1&in_stock=true"
        if ($catalog.total -gt 0) {
            Start-Process "http://127.0.0.1:3000"
            Write-Host "PC Configurator is ready: http://127.0.0.1:3000"
            exit 0
        }
    } catch {}
    Start-Sleep -Seconds 3
} while ((Get-Date) -lt $deadline)
throw "Services did not become ready. Run: docker compose logs api frontend db"
