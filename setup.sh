#!/bin/bash

# Trading Dashboard - One-time Setup Script
# Run this ONCE after cloning the repository and copying .env file

echo "🚀 Setting up Trading Dashboard..."

# Check if we're in the right directory
if [ ! -f "README.md" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    echo "❌ Error: backend/.env file not found!"
    echo "Please copy your .env file to backend/.env first"
    exit 1
fi

echo "📦 Installing backend dependencies..."
cd backend

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python3 is not installed"
    echo "Please install Python 3.9+ first: brew install python@3.9"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
echo "📥 Installing Python packages..."
source venv/bin/activate
pip install --upgrade pip

# Install packages with dependency resolution if requirements.txt fails
echo "🔧 Installing packages with dependency resolution..."
if ! pip install -r requirements.txt; then
    echo "⚠️  Requirements.txt failed, trying without version constraints..."
    pip install fastapi "uvicorn[standard]" python-dotenv pydantic pydantic-settings httpx requests yfinance praw pandas numpy beautifulsoup4 lxml feedparser redis supabase gotrue PyJWT python-multipart textblob anthropic
fi

cd ../frontend

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is not installed"
    echo "Please install Node.js 18+: brew install node"
    exit 1
fi

echo "📥 Installing Node.js packages..."
npm install

cd ..

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "⚠️  Warning: Docker is not running"
    echo "Please start Docker Desktop, then run: docker-compose up -d"
else
    echo "🐳 Starting Redis with Docker..."
    docker-compose up -d
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Make sure Docker is running: docker-compose up -d"
echo "2. Start the application: ./start.sh"
echo "3. Open http://localhost:3000 in your browser"