#!/bin/bash

# Trading Dashboard - Stop Script
# Cleanly stops all running services

echo "🛑 Stopping Trading Dashboard..."

# Function to kill process by PID file
kill_by_pid() {
    if [ -f "$1" ]; then
        PID=$(cat "$1")
        if kill -0 "$PID" 2>/dev/null; then
            echo "🔄 Stopping $2 (PID: $PID)..."
            kill "$PID" 2>/dev/null
            # Wait for graceful shutdown
            sleep 3
            # Force kill if still running
            if kill -0 "$PID" 2>/dev/null; then
                kill -9 "$PID" 2>/dev/null
            fi
        fi
        rm -f "$1"
    fi
}

# Function to kill process on port
kill_port() {
    if lsof -ti:$1 > /dev/null 2>&1; then
        echo "🔄 Stopping process on port $1..."
        lsof -ti:$1 | xargs kill -9 2>/dev/null || true
    fi
}

# Stop using PID files first
kill_by_pid ".backend.pid" "Backend"
kill_by_pid ".frontend.pid" "Frontend"

# Fallback: stop by port
kill_port 8000  # Backend
kill_port 3000  # Frontend

# Optionally stop Redis (uncomment if you want to stop Redis too)
# echo "🐳 Stopping Redis..."
# docker-compose down

echo "✅ All services stopped"

# Clean up log files older than 7 days
if [ -d "logs" ]; then
    find logs -name "*.log" -mtime +7 -delete 2>/dev/null || true
fi