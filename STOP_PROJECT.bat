@echo off
setlocal
cd /d "%~dp0"
docker compose down --remove-orphans
echo PC Configurator stopped.
pause
