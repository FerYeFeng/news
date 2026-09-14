@echo off
setlocal
pushd "%~dp0"
set "NEWS_REFRESH_WINDOW_SECONDS=540"

python --version >nul 2>nul
if not errorlevel 1 (
  python "%~dp0serve.py"
  goto done
)

py -3 --version >nul 2>nul
if not errorlevel 1 (
  py -3 "%~dp0serve.py"
  goto done
)

echo Python 3 was not found. Install Python 3 first.
pause

:done
if errorlevel 1 pause
popd
