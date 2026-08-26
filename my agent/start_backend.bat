@echo off
echo Starting TASKFINISHER AI Backend...
echo.

if not exist .env (
    echo ERROR: .env file not found!
    echo Please create a .env file with your GOOGLE_API_KEY
    exit /b 1
)

echo Loading environment variables...
for /f "usebackq delims=" %%a in (.env) do (
    set "%%a"
)

echo Environment loaded from .env.

echo.
echo Starting backend server...
python main.py
