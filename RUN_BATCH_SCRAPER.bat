@echo off
title Batch Contact Scraper
color 0A

echo ========================================
echo   BATCH CONTACT SCRAPER
echo   Industrial Version
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Python not found!
    echo.
    echo Install Python from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [OK] Python detected
echo.

REM Check packages
echo Checking packages...
python -c "import pandas, requests, bs4, openpyxl" 2>nul
if %errorlevel% neq 0 (
    echo.
    echo [WARN] Installing packages...
    pip install pandas openpyxl requests beautifulsoup4 lxml
    echo.
)

echo [OK] All packages ready
echo.
echo ========================================
echo.

REM Run batch scraper
python batch_scraper.py

echo.
pause
