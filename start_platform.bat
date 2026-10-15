@echo off
TITLE Enterprise E-Commerce Big Data Lakehouse Platform
COLOR 0A
cls
echo ===============================================================================
echo        ENTERPRISE E-COMMERCE BIG DATA LAKEHOUSE PLATFORM (OLIST 100K)
echo ===============================================================================
echo.
echo [1/2] Verifying Python Environment...
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    pause
    exit /b 1
)

echo.
echo [2/2] Launching Full Pipeline and D3.js Visualizer...
python run_pipeline.py --port 8050
pause
