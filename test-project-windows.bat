@echo off
setlocal EnableExtensions
cd /d "%~dp0"

where docker >nul 2>nul || (
  echo ERROR: Docker Desktop is required.
  pause
  exit /b 1
)
docker info >nul 2>nul || (echo ERROR: Docker Desktop is not running. & pause & exit /b 1)
if not exist .env copy .env.example .env >nul

echo [1/6] Build images
docker compose build || goto :failed
echo [2/6] Start PostgreSQL stack
docker compose up -d || goto :failed
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$d=(Get-Date).AddMinutes(4); do { try { if ((Invoke-RestMethod -TimeoutSec 5 http://127.0.0.1:8000/api/v1/health/ready).status) { exit 0 } } catch {}; Start-Sleep 3 } while ((Get-Date)-lt $d); exit 1" || goto :failed
echo [3/6] PostgreSQL migration
docker compose exec -T api alembic current || goto :failed
echo [4/6] Backend tests and Ruff
docker compose exec -T api python -m pytest -q || goto :failed
docker compose exec -T api python -m ruff check . || goto :failed
docker compose exec -T api python -m ruff format --check . || goto :failed
echo [5/6] Live API smoke test
docker compose exec -T api python scripts/smoke_test.py || goto :failed
echo [6/6] Frontend proxy
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$r=Invoke-RestMethod -TimeoutSec 10 'http://127.0.0.1:3000/api-backend/products?limit=1&in_stock=true'; if ($r.total -lt 1) { exit 1 }" || goto :failed

echo ALL TESTS PASSED
pause
exit /b 0

:failed
echo TESTS FAILED. See the error above.
pause
exit /b 1
