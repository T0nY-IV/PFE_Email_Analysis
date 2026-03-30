@echo off
echo Starting email_refresher.py and api.py in separate CMD windows...
echo.

start "API Server" cmd /k "python api.py"

REM Wait 60 seconds before starting email_refresher.py
echo Waiting 60 seconds before starting Email Refresher...
timeout /t 60 /nobreak >nul
start "Email Refresher" cmd /k "python email_refresher.py"

echo Both scripts have been launched in separate windows.
echo.
echo Email Refresher window: Runs email polling and processing
echo API Server window: Runs FastAPI server on port 8086
echo.
pause
