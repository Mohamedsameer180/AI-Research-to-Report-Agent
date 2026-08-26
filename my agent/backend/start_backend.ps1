# Backend startup script for TASKFINISHER AI
Write-Host "Starting TASKFINISHER AI Backend..."
Set-Location (Join-Path $PSScriptRoot "..")
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -and -not $_.TrimStart().StartsWith("#")) {
            $name, $value = $_ -split "=", 2
            if ($name) {
                [Environment]::SetEnvironmentVariable($name.Trim(), $value, "Process")
            }
        }
    }
    Write-Host "Environment loaded from .env."
} else {
    Write-Host "No .env file found. The deterministic demo still works without live model calls."
}
Write-Host "Starting backend server..."
python main.py
