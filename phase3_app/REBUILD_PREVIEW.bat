@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
 echo Run START_WINDOWS.bat once to install the Python environment, then close the app and try again.
 pause
 exit /b 1
)
.venv\Scripts\python.exe build_preview.py
if errorlevel 1 (
 echo Build failed. See the error above.
 pause
 exit /b 1
)
start "" "%~dp0OPEN_PREVIEW.html"
pause
