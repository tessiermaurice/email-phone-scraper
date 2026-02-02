@echo off
title Contact Scraper
color 0A

echo ================================================================
echo              EMAIL ^& PHONE NUMBER SCRAPER v2.0
echo ================================================================
echo.

REM Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Python not found!
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [OK] Python detected
echo.

REM Check required packages
echo Checking required packages...
python -c "import pandas, requests, bs4, openpyxl" 2>nul
if %errorlevel% neq 0 (
    echo.
    echo [WARN] Missing packages detected. Installing...
    echo.
    pip install pandas openpyxl requests beautifulsoup4 lxml
    echo.
)

echo [OK] All packages ready
echo.
echo ================================================================
echo.

REM Run the scraper
python contact_scraper.py

echo.
echo ================================================================
echo                         COMPLETED
echo ================================================================
echo.
pause
