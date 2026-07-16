@echo off
setlocal
cd /d "%~dp0"
echo ===== CONTAINERS =====
docker compose ps -a
echo.
echo ===== API LAST 80 LINES =====
docker compose logs --no-color --tail=80 api
echo.
echo ===== FRONTEND LAST 80 LINES =====
docker compose logs --no-color --tail=80 frontend
pause
