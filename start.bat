@echo off
chcp 65001 >nul
title CAD Translator v2.0
echo ========================================================
echo   CAD PDF Translator v2.0 - Furniture Edition
echo   Hybrid Architecture: Vector | EasyOCR | Template
echo ========================================================
echo.
echo Starting server...
echo Open http://localhost:5000 in your browser
echo Press Ctrl+C to stop
echo.

cd /d "%~dp0"

:: Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

:: Run the app
python app.py
pause
