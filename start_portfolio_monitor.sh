#!/bin/bash

# AI Hedge Fund Portfolio Monitor Startup Script
# This script starts both the backend API server and frontend web interface

set -e  # Exit on any error

echo "🚀 Starting AI Hedge Fund Portfolio Monitor"
echo "============================================"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Please run this script from the ai-hedge-fund root directory"
    exit 1
fi

# Check environment variables
echo "🔧 Checking environment..."
if [ -z "$ZERODHA_API_KEY" ] || [ -z "$ZERODHA_ACCESS_TOKEN" ]; then
    echo "⚠️  Warning: Zerodha credentials not found in environment"
    echo "   Portfolio monitoring will run in demo mode"
    echo "   Run 'python generate_zerodha_token.py' to set up credentials"
else
    echo "✅ Zerodha credentials found"
fi

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo "   Backend stopped"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo "   Frontend stopped"
    fi
    echo "👋 Goodbye!"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check if ports are available
check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "❌ Error: Port $port is already in use (needed for $service)"
        echo "   Please stop the service using port $port and try again"
        exit 1
    fi
}

check_port 8000 "backend API"
check_port 5173 "frontend dev server"

# Install dependencies if needed
echo "📦 Checking dependencies..."
if [ ! -d "node_modules" ] || [ ! -d "app/frontend/node_modules" ]; then
    echo "   Installing frontend dependencies..."
    cd app/frontend
    npm install
    cd ../..
fi

# Start backend
echo "🔧 Starting backend API server..."
cd app/backend
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ../..

# Wait for backend to start
echo "   Waiting for backend to start..."
sleep 3

# Check if backend started successfully
if ! curl -s http://localhost:8000/portfolio/health >/dev/null 2>&1; then
    echo "⚠️  Backend may not have started properly, but continuing..."
else
    echo "✅ Backend API server started on http://localhost:8000"
fi

# Start frontend
echo "🎨 Starting frontend web interface..."
cd app/frontend
npm run dev &
FRONTEND_PID=$!
cd ../..

# Wait for frontend to start
echo "   Waiting for frontend to start..."
sleep 5

echo ""
echo "🎉 Portfolio Monitor is now running!"
echo "=================================="
echo ""
echo "📊 Web Interface:     http://localhost:5173"
echo "🔧 API Documentation: http://localhost:8000/docs"
echo "💓 Health Check:      http://localhost:8000/portfolio/health"
echo "📡 Live Stream:       http://localhost:8000/portfolio/stream"
echo ""
echo "💡 Tips:"
echo "   • Switch between 'Portfolio Monitor' and 'AI Agents Flow' tabs"
echo "   • Portfolio data updates every 30 seconds automatically"
echo "   • Use the refresh button for manual updates"
echo ""
echo "🔍 Troubleshooting:"
echo "   • If portfolio shows errors, check Zerodha credentials"
echo "   • Run 'python test_portfolio_monitor.py' to test the system"
echo "   • Check logs above for any startup errors"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Keep script running and wait for user to stop
wait $BACKEND_PID $FRONTEND_PID 