@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ui = $false; $api = $false; $catalog = $false; try { $ui = (Invoke-WebRequest -UseBasicParsing -TimeoutSec 5 http://127.0.0.1:3000).StatusCode -eq 200 } catch {}; try { $api = (Invoke-RestMethod -TimeoutSec 5 http://127.0.0.1:3000/api-backend/health).status -eq 'ok' } catch {}; try { $catalog = (Invoke-RestMethod -TimeoutSec 10 'http://127.0.0.1:3000/api-backend/products?limit=1&in_stock=true').total -gt 0 } catch {}; if ($ui -and $api -and $catalog) { Write-Host 'OK: frontend, API and priced catalog are available.'; exit 0 } else { Write-Host 'ERROR: stack is unavailable. Run START_WINDOWS_FIXED.cmd'; exit 1 }"
pause
exit /b %ERRORLEVEL%
