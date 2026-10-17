@echo off
setlocal
cd /d "%~dp0"
echo Starting NEORORA practice demo...
if exist .venv\Scripts\python.exe goto install
where py >nul 2>nul
if errorlevel 1 goto usepython
py -3 -m venv .venv
goto checkvenv
:usepython
python -m venv .venv
:checkvenv
if not exist .venv\Scripts\python.exe (
  echo Python 3.10 or newer is needed. Install Python, then try again.
  pause
  exit /b 1
)
:install
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
  echo Installation failed. Check the error above and your internet connection.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m streamlit run app.py
pause
