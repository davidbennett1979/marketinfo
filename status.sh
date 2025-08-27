#!/bin/bash

# Trading Dashboard - Status Check Script
# Check if all services are running properly

echo "📊 Trading Dashboard Status Check"
echo "=================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if port is in use
check_port() {
    if lsof -ti:$1 > /dev/null 2>&1; then
        echo -e "✅ $2: ${GREEN}Running${NC} on port $1"
        return 0
    else
        echo -e "❌ $2: ${RED}Not running${NC} on port $1"
        return 1
    fi
}

# Function to check HTTP endpoint
check_endpoint() {
    if curl -s "$1" > /dev/null 2>&1; then
        echo -e "✅ $2: ${GREEN}Responding${NC} at $1"
        return 0
    else
        echo -e "❌ $2: ${RED}Not responding${NC} at $1"
        return 1
    fi
}

echo ""
echo "🔍 Port Status:"
check_port 3000 "Frontend"
check_port 8000 "Backend"
check_port 6379 "Redis"

echo ""
echo "🌐 HTTP Status:"
check_endpoint "http://localhost:3000" "Frontend"
check_endpoint "http://localhost:8000/health" "Backend Health"
check_endpoint "http://localhost:8000/docs" "API Docs"

echo ""
echo "🐳 Docker Status:"
if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "redis"; then
    echo -e "✅ Redis Container: ${GREEN}Running${NC}"
    docker ps --format "table {{.Names}}\t{{.Status}}" | grep redis
else
    echo -e "❌ Redis Container: ${RED}Not running${NC}"
fi

echo ""
echo "📁 Process Status:"
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    if kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo -e "✅ Backend Process: ${GREEN}Running${NC} (PID: $BACKEND_PID)"
    else
        echo -e "❌ Backend Process: ${RED}Dead${NC} (PID file exists but process not found)"
    fi
else
    echo -e "⚠️  Backend Process: ${YELLOW}No PID file${NC}"
fi

if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if kill -0 "$FRONTEND_PID" 2>/dev/null; then
        echo -e "✅ Frontend Process: ${GREEN}Running${NC} (PID: $FRONTEND_PID)"
    else
        echo -e "❌ Frontend Process: ${RED}Dead${NC} (PID file exists but process not found)"
    fi
else
    echo -e "⚠️  Frontend Process: ${YELLOW}No PID file${NC}"
fi

echo ""
echo "📋 Quick Links:"
echo "• Frontend: http://localhost:3000"
echo "• Backend API: http://localhost:8000"
echo "• API Documentation: http://localhost:8000/docs"
echo "• Logs: ./logs/"

echo ""
echo "🔧 Useful Commands:"
echo "• Start: ./start.sh"
echo "• Stop: ./stop.sh"
echo "• Logs: tail -f logs/backend.log"