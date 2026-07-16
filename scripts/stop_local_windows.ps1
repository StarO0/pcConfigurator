$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
$runDirectory = Join-Path $root ".run"
$stopped = $false

foreach ($name in @("frontend", "api")) {
    $pidFile = Join-Path $runDirectory "$name.pid"
    if (Test-Path $pidFile) {
        $processId = (Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
        if ($processId -match '^\d+$') {
            & taskkill.exe /PID $processId /T /F 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) { $stopped = $true }
        }
        Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    }
}

# npm can create a child node.exe with another PID. Stop the actual listeners too.
foreach ($port in @(3000, 8000)) {
    $owners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($processId in $owners) {
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        $stopped = $true
    }
}

if (Get-Command docker -ErrorAction SilentlyContinue) {
    Push-Location $root
    try { & docker compose down 2>$null | Out-Null } finally { Pop-Location }
}

if ($stopped) {
    Write-Host "PC Configurator stopped. Ports 3000 and 8000 are free."
} else {
    Write-Host "PC Configurator was not running."
}
exit 0
