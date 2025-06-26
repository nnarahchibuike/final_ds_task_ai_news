@echo off
REM DS Task AI News - Setup Script for Windows
REM This script sets up the development environment

echo 🚀 Setting up DS Task AI News...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is required but not installed.
    echo Please install Python 3.8 or higher and try again.
    pause
    exit /b 1
)

echo ✅ Python found

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️ Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo 📚 Installing dependencies...
cd backend
pip install -r requirements.txt
cd ..

REM Create data directories
echo 📁 Creating data directories...
if not exist "data\raw_news" mkdir data\raw_news
if not exist "data\processed_news" mkdir data\processed_news

REM Copy environment template if .env doesn't exist
if not exist ".env" (
    echo ⚙️ Creating environment configuration...
    copy .env.example .env
    echo ✅ Environment template created at .env
    echo ⚠️  Please edit .env and add your API keys before running the application
) else (
    echo ✅ Environment configuration already exists
)

echo.
echo 🎉 Setup completed successfully!
echo.
echo Next steps:
echo 1. Edit .env file and add your API keys:
echo    - COHERE_API_KEY=your_cohere_api_key
echo    - GROQ_API_KEY=your_groq_api_key
echo    - PINECONE_API_KEY=your_pinecone_api_key
echo.
echo 2. Run the API server:
echo    run.bat
echo.
echo 3. Or activate the virtual environment manually:
echo    venv\Scripts\activate.bat
echo    cd backend && python main.py
echo.
echo 4. Access the API:
echo    - API: http://localhost:8000
echo    - Documentation: http://localhost:8000/docs
echo.
echo 📖 For more information, see docs\API_Documentation.md

pause
