@echo off
echo ========================================================
echo Starting TASKFINISHER AI System (Full Stack)
echo ========================================================
echo.

cd /d "%~dp0"

if exist .env (
    echo Loading environment variables from .env...
    for /f "usebackq delims=" %%a in (.env) do (
        set "%%a"
    )
) else (
    echo No .env file found. The deterministic demo still works without live model calls.
)

set PYTHON_EXE=python
if exist "C:\Users\HP\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe" (
    set "PYTHON_EXE=C:\Users\HP\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe"
) else if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
)

echo.
echo [1/2] Starting backend server on http://localhost:8000 using %PYTHON_EXE%...
start "TASKFINISHER AI Backend" "%PYTHON_EXE%" main.py

echo.
echo [2/2] Starting frontend development server on http://localhost:5173...
start "TASKFINISHER AI Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================================
echo TASKFINISHER AI System is running!
echo Backend API:     http://localhost:8000
echo Frontend UI:     http://localhost:5173
echo API Docs:        http://localhost:8000/docs
echo ========================================================
echo.
pause
