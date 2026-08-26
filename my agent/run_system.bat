@echo off
echo Starting TASKFINISHER AI System...
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
echo Starting backend server...
start "" python main.py

echo.
echo Starting frontend development environment...
call npm run dev

echo.
echo TASKFINISHER AI System is running!
echo Backend API: http://localhost:8000
echo Frontend UI: http://localhost:5173
echo API Documentation: http://localhost:8000/docs
echo.
echo To stop the system, close these windows or use Task Manager.
echo.
pause
