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
set PYTHON_EXE=python
if exist "C:\Users\HP\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe" (
    set "PYTHON_EXE=C:\Users\HP\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe"
) else if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
)
echo Starting backend with %PYTHON_EXE%...
"%PYTHON_EXE%" main.py
