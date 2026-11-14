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

echo.
echo [1/2] Starting backend server on http://localhost:8000...
start "TASKFINISHER AI Backend" python main.py

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
