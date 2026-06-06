@echo off
echo ============================================
echo   CAD Translator - Starting Server
echo ============================================

cd /d "%~dp0"

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.9+
    pause
    exit /b 1
)

:: Check/Install dependencies
echo Checking dependencies...
pip install -r requirements.txt -q

:: Start server
echo.
echo Starting server at http://localhost:5000
echo Press Ctrl+C to stop
echo.
python app.py

pause
