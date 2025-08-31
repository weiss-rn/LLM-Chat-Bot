@echo off
:: Script: run_app.bat
:: Runs generate_secrets.py, then starts streamlit app

:: Enable delayed expansion for error checks
setlocal enabledelayedexpansion

:: Go to script directory
cd /d "%~dp0"

echo Running generate_secrets.py...
python generate_secrets.py

if %errorlevel% neq 0 (
    echo Error: generate_secrets.py failed!
    pause
    exit /b 1
)

echo Starting Streamlit app (streamlit_app_v2.py)...
echo Press Ctrl+C to stop the server.

:: Run the Streamlit app
python -m streamlit run streamlit_app_v2.py

:: Graceful exit message
echo.
echo Streamlit app stopped.
pause