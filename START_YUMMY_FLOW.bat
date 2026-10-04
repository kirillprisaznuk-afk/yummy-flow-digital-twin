@echo off
setlocal
cd /d "%~dp0"
if not exist "%~dp0.venv\Scripts\python.exe" (
  echo The project Python environment is missing. See RUNNING_THE_APP.md.
  pause
  exit /b 1
)
"%~dp0.venv\Scripts\python.exe" "%~dp0scripts\launcher.py" start
set "result=%ERRORLEVEL%"
if /I not "%~1"=="--no-pause" pause
exit /b %result%
