@echo off
cd /d "%~dp0"
python -m venv .venv
if errorlevel 1 exit /b 1
.venv\Scripts\python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
call npm --prefix frontend ci --no-audit --no-fund
if errorlevel 1 exit /b 1
call npm --prefix frontend run build
if errorlevel 1 exit /b 1
echo Installation complete. Run RUN_CLIP_ASSASSIN.bat.
pause
