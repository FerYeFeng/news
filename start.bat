@echo off
setlocal
chcp 65001 >nul
pushd "%~dp0"

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

echo 未找到 Python 3，请先安装 Python 3。
pause

:done
if errorlevel 1 pause
popd
