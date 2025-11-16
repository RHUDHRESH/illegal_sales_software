@echo off
REM Raptorflow Lead Engine - Windows Development Startup

echo 🚀 Raptorflow Lead Engine - Starting...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Install Python 3.9+ first.
    pause
    exit /b 1
)
echo ✅ Python is installed

REM Create venv if not exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate venv
echo 🔌 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📚 Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Check Ollama
echo.
echo 📡 Checking Ollama...
timeout /t 1 /nobreak >nul 2>&1
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Ollama not running at http://localhost:11434
    echo    Start Ollama first in another terminal:
    echo    ollama serve
    pause
    exit /b 1
)
echo ✅ Ollama is running

REM Start API
echo.
echo 🎯 Starting FastAPI server on http://127.0.0.1:8000
echo 📚 Docs at http://127.0.0.1:8000/docs
echo.
uvicorn main:app --reload --host 127.0.0.1 --port 8000

pause
