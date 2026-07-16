@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title PC Configurator - Full Reset

echo WARNING: this deletes the LOCAL PostgreSQL and Redis data for this project.
choice /C YN /M "Reset and start from a clean database"
if errorlevel 2 exit /b 0

where docker >nul 2>nul || goto :no_docker
docker info >nul 2>nul || goto :docker_not_running

docker compose down -v --remove-orphans
if errorlevel 1 (
  echo Could not stop the previous stack.
  pause
  exit /b 1
)
docker builder prune -f >nul 2>nul
call "%~dp0START_PROJECT.bat"
exit /b %ERRORLEVEL%

:no_docker
echo Docker Desktop is not installed.
pause
exit /b 1
:docker_not_running
echo Start Docker Desktop first.
pause
exit /b 1
