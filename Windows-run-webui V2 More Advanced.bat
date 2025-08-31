@echo off

REM
cd chatbot-webv2

REM
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Please install Python first.
    pause
    exit /b 1
)

REM
echo Running generate_secrets.py...
python generate_secrets.py

echo Running app.py...
python app.py

REM
cd ..

pause