@echo off
REM DS Task AI News - Run Script for Windows
REM This script starts the FastAPI backend server

echo 🚀 Starting DS Task AI News API Server...

REM Check if virtual environment exists
if not exist "venv" (
    echo ❌ Virtual environment not found.
    echo Please run setup.bat first to set up the project.
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo ❌ Environment configuration (.env) not found.
    echo Please copy .env.example to .env and configure your API keys.
    pause
    exit /b 1
)

REM Check if API keys are configured (basic check)
findstr /C:"COHERE_API_KEY=your_cohere_api_key_here" .env >nul
if not errorlevel 1 (
    echo ⚠️  Warning: Cohere API key may not be configured properly in .env file
)

findstr /C:"GROQ_API_KEY=your_groq_api_key_here" .env >nul
if not errorlevel 1 (
    echo ⚠️  Warning: Groq API key may not be configured properly in .env file
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Change to backend directory
cd backend

REM Check if all dependencies are installed
echo 📚 Checking dependencies...
python -c "import fastapi, uvicorn, pinecone, cohere, groq" 2>nul
if errorlevel 1 (
    echo ❌ Some dependencies are missing.
    echo Please run setup.bat to install dependencies.
    pause
    exit /b 1
)

echo ✅ All dependencies found

REM Start the API server
echo 🌟 Starting FastAPI server...
echo.
echo 📍 API will be available at:
echo    - Main API: http://localhost:8000
echo    - Interactive Docs: http://localhost:8000/docs
echo    - Alternative Docs: http://localhost:8000/redoc
echo.
echo Press Ctrl+C to stop the server
echo.

REM Run with uvicorn
python main.py

pause
