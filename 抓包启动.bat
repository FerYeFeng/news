@echo off
setlocal
title Bus Monitor Launcher

set "NEWS_DIR=D:\news"
set "BUS_DIR=D:\bus-route-monitor"

if not exist "%NEWS_DIR%\start.bat" (
  echo [ERROR] Missing %NEWS_DIR%\start.bat
  goto failed
)

if not exist "%BUS_DIR%\start.bat" (
  echo [ERROR] Missing %BUS_DIR%\start.bat
  goto failed
)

call :is_listening 9092
if errorlevel 1 (
  echo [START] News monitor: http://localhost:9092
  start "News Monitor" /belownormal /D "%NEWS_DIR%" cmd /c call start.bat
) else (
  echo [RUNNING] News monitor: http://localhost:9092
)

call :is_listening 9093
if errorlevel 1 (
  echo [START] Weibo monitor: http://localhost:9093
  start "Weibo Monitor" /belownormal /D "%BUS_DIR%" cmd /c call start.bat
) else (
  echo [RUNNING] Weibo monitor: http://localhost:9093
)

echo.
echo Both services have been checked.
ping -n 4 127.0.0.1 >nul
exit /b 0

:is_listening
powershell -NoProfile -Command "$connection = Get-NetTCPConnection -State Listen -LocalPort %1 -ErrorAction SilentlyContinue; if ($connection) { exit 0 } else { exit 1 }" >nul 2>nul
exit /b %errorlevel%

:failed
echo.
echo Startup failed. Check the paths above.
pause
exit /b 1
