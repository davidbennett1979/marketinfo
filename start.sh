#!/bin/bash

# Trading Dashboard - Start Script
# Run this every time you want to start the application

echo "🚀 Starting Trading Dashboard..."

# Check if we're in the right directory
if [ ! -f "README.md" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Function to check if a port is in use
port_in_use() {
    lsof -ti:$1 > /dev/null
}

# Function to kill process on port
kill_port() {
    if port_in_use $1; then
        echo "🔄 Stopping existing process on port $1..."
        lsof -ti:$1 | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

# Stop any existing processes
kill_port 8000  # Backend
kill_port 3000  # Frontend

# Start Redis if not running
if ! docker ps | grep -q redis; then
    echo "🐳 Starting Redis..."
    docker-compose up -d
    sleep 3
fi

# Create log directory
mkdir -p logs

echo "🐍 Starting backend server..."
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found!"
    echo "Please run ./setup.sh first"
    exit 1
fi

# Start backend in background
source venv/bin/activate
nohup python main.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend started successfully on http://localhost:8000"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Backend failed to start. Check logs/backend.log"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

cd ../frontend

echo "🌐 Starting frontend server..."
# Start frontend in background
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to start
echo "⏳ Waiting for frontend to start..."
for i in {1..30}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ Frontend started successfully on http://localhost:3000"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Frontend failed to start. Check logs/frontend.log"
        kill $FRONTEND_PID 2>/dev/null || true
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

cd ..

# Save PIDs for stop script
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

echo ""
echo "🎉 Trading Dashboard is running!"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "💡 Logs are in the logs/ directory"
echo "🛑 To stop: ./stop.sh"
echo ""
echo "🤖 Try the AI chat with Cmd/Ctrl + K"