@echo off
rem Windows cmd/PowerShell launcher for search.py
setlocal
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
for %%P in ("py -3" python python3) do (
  %%~P -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1 && (
    %%~P "%~dp0search.py" %*
    goto :done
  )
)
echo ui-ux-pro-max: Python 3.8+ not found. Install with: winget install Python.Python.3.12 1>&2
exit /b 127
:done
exit /b %errorlevel%
