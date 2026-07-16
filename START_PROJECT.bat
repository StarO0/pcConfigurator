@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title PC Configurator - Start

echo ==============================================
echo        PC CONFIGURATOR - ONE CLICK START
echo ==============================================
echo.

where docker >nul 2>nul
if errorlevel 1 goto :no_docker

docker info >nul 2>nul
if errorlevel 1 goto :docker_not_running

if not exist ".env" (
  copy /Y ".env.example" ".env" >nul
  echo Created local .env file.
)

echo [1/4] Checking Docker Compose configuration...
docker compose config >nul
if errorlevel 1 goto :compose_error

echo [2/4] Building and starting containers...
docker compose up -d --build --remove-orphans
if errorlevel 1 goto :startup_error

echo [3/4] Waiting for API and frontend...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "$deadline=(Get-Date).AddMinutes(8); $api=$false; $front=$false; while((Get-Date)-lt $deadline){ try{$r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 5 http://127.0.0.1:8000/api/v1/health/live; $api=($r.StatusCode -eq 200)}catch{$api=$false}; try{$r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 5 http://127.0.0.1:3000; $front=($r.StatusCode -eq 200)}catch{$front=$false}; if($api -and $front){exit 0}; Start-Sleep -Seconds 3}; exit 1"
if errorlevel 1 goto :not_ready

echo [4/4] Project is ready.
echo.
echo Site:      http://localhost:3000
echo API docs: http://localhost:8000/docs
echo Admin:    admin@pcbuilder.app / Local-admin-123
echo.
start "" http://localhost:3000
exit /b 0

:no_docker
echo ERROR: Docker Desktop is not installed.
echo Install Docker Desktop, restart Windows, then run this file again.
echo https://www.docker.com/products/docker-desktop/
pause
exit /b 1

:docker_not_running
echo ERROR: Docker Desktop is installed but not running.
echo Open Docker Desktop and wait until it says "Engine running".
pause
exit /b 1

:compose_error
echo ERROR: docker-compose.yml is invalid.
docker compose config
pause
exit /b 1

:startup_error
echo ERROR: Docker could not build or start the project.
goto :show_logs

:not_ready
echo ERROR: Containers started, but the site did not become ready.
:show_logs
echo.
echo Saving diagnostics to STARTUP_ERROR_LOG.txt ...
(
  echo ===== docker compose ps =====
  docker compose ps -a
  echo.
  echo ===== API LOGS =====
  docker compose logs --no-color --tail=200 api
  echo.
  echo ===== FRONTEND LOGS =====
  docker compose logs --no-color --tail=200 frontend
  echo.
  echo ===== DATABASE LOGS =====
  docker compose logs --no-color --tail=100 db
) > STARTUP_ERROR_LOG.txt 2>&1

docker compose ps -a
echo.
echo Diagnostics: %CD%\STARTUP_ERROR_LOG.txt
echo Send this file if the problem remains.
pause
exit /b 1
