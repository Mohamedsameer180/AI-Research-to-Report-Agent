@echo off
echo Starting TASKFINISHER AI Backend...
cd /d "%~dp0\.."
if exist .env (
    for /f "usebackq delims=" %%a in (.env) do (
        set "%%a"
    )
    echo Environment loaded from .env.
) else (
    echo No .env file found. The deterministic demo still works without live model calls.
)
echo Starting backend...
python main.py
