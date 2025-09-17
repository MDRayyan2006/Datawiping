@echo off
echo ========================================
echo DataWipe Application Startup Script
echo ========================================
echo.

echo Starting FastAPI Backend...
start "DataWipe Backend" cmd /k "cd /d C:\datawi && python main.py"

echo.
echo Waiting for backend to start...
timeout /t 5 /nobreak > nul

echo.
echo Starting Flutter App...
start "DataWipe Flutter App" cmd /k "cd /d C:\datawi\flutter_app && C:\datawi\flutter\bin\flutter.bat run -d windows"

echo.
echo ========================================
echo Both applications are starting...
echo.
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Flutter App: Will open in a new window
echo.
echo Press any key to exit this script...
pause > nul
