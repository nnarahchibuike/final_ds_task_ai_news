#!/bin/bash

# DS Task AI News - Setup Script
# This script sets up the development environment

set -e  # Exit on any error

echo "🚀 Setting up DS Task AI News..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.8 or higher and try again."
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python $python_version found"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
cd backend
pip install -r requirements.txt
cd ..

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/raw_news
mkdir -p data/processed_news

# Copy environment template if .env doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️ Creating environment configuration..."
    cp .env.example .env
    echo "✅ Environment template created at .env"
    echo "⚠️  Please edit .env and add your API keys before running the application"
else
    echo "✅ Environment configuration already exists"
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your API keys:"
echo "   - COHERE_API_KEY=your_cohere_api_key"
echo "   - GROQ_API_KEY=your_groq_api_key"
echo "   - PINECONE_API_KEY=your_pinecone_api_key"
echo ""
echo "2. Run the complete application:"
echo "   ./run.sh"
echo ""
echo "3. Or activate the virtual environment manually:"
echo "   source venv/bin/activate"
echo "   cd backend && python main.py"
echo ""
echo "4. Access the application:"
echo "   - 🌐 Frontend (Web UI): http://localhost:8000"
echo "   - 📡 API Endpoints: http://localhost:8000/fetch-news, /recommend-news"
echo "   - 📚 API Documentation: http://localhost:8000/docs"
echo ""
echo "5. To refresh news articles:"
echo "   python pipeline.py"
echo ""
echo "📖 For more information, see docs/API_Documentation.md"
