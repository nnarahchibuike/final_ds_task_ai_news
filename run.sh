#!/bin/bash

# DS Task AI News - Run Script
# This script starts the FastAPI backend server

set -e  # Exit on any error

echo "🚀 Starting DS Task AI News API Server..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found."
    echo "Please run ./setup.sh first to set up the project."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Environment configuration (.env) not found."
    echo "Please copy .env.example to .env and configure your API keys."
    exit 1
fi

# Check if API keys are configured (check for placeholder values)
if grep -q "COHERE_API_KEY=your_cohere_api_key_here" .env || grep -q "GROQ_API_KEY=your_groq_api_key_here" .env || grep -q "PINECONE_API_KEY=your_pinecone_api_key_here" .env; then
    echo "⚠️  Warning: API keys may not be configured properly in .env file"
    echo "Please make sure to set your actual API keys before using the application."
else
    echo "✅ API keys appear to be configured"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Change to backend directory
cd backend

# Check if all dependencies are installed
echo "📚 Checking dependencies..."
if ! python -c "import fastapi, uvicorn, pinecone, cohere, groq, feedparser; from bs4 import BeautifulSoup" 2>/dev/null; then
    echo "❌ Some dependencies are missing."
    echo "Please run ./setup.sh to install dependencies."
    exit 1
fi

echo "✅ All dependencies found"

# Start the API server
echo "🌟 Starting AI News Hub application..."
echo ""
echo "📍 Application will be available at:"
echo "   - 🌐 Frontend (Web UI): http://localhost:8000"
echo "   - 📡 API Endpoints: http://localhost:8000/fetch-news, /recommend-news"
echo "   - 📚 API Documentation: http://localhost:8000/docs"
echo "   - 📖 Alternative Docs: http://localhost:8000/redoc"
echo ""
echo "💡 The frontend automatically calls /fetch-news on startup"
echo "💡 To refresh articles, run: python ../pipeline.py"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run with uvicorn
python main.py
