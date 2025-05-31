#!/bin/bash

# AI Stock Opportunities System - Quick Start Script
echo "🚀 Starting AI Stock Opportunities System..."
echo "================================================"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Please run this script from the ai-hedge-fund root directory"
    exit 1
fi

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Port $1 is already in use"
        return 1
    else
        return 0
    fi
}

# Check ports
echo "🔍 Checking ports..."
if ! check_port 8000; then
    echo "   Backend port 8000 is busy - stopping existing process"
    pkill -f "uvicorn.*main:app.*8000" || true
    sleep 2
fi

if ! check_port 5173; then
    echo "   Frontend port 5173 is busy - stopping existing process"
    pkill -f "vite.*5173" || true
    sleep 2
fi

# Install dependencies
echo "📦 Installing dependencies..."
poetry install --quiet

# Start backend in background
echo "🔧 Starting backend server..."
cd app/backend
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ../../backend.log 2>&1 &
BACKEND_PID=$!
cd ../..

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "✅ Backend started successfully!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Backend failed to start. Check backend.log for errors."
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done

# Start frontend in background
echo "🎨 Starting frontend server..."
cd app/frontend
npm run dev > ../../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ../..

# Wait for frontend to start
echo "⏳ Waiting for frontend to start..."
for i in {1..30}; do
    if curl -s http://localhost:5173 > /dev/null 2>&1; then
        echo "✅ Frontend started successfully!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Frontend failed to start. Check frontend.log for errors."
        kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done

# Test the system
echo "🧪 Running quick system test..."
python test_opportunities_system.py

echo ""
echo "🎉 AI STOCK OPPORTUNITIES SYSTEM IS READY!"
echo "================================================"
echo ""
echo "🌐 Access Points:"
echo "   • Frontend:    http://localhost:5173"
echo "   • Backend API: http://localhost:8000"
echo "   • API Docs:    http://localhost:8000/docs"
echo ""
echo "📱 Quick Test Steps:"
echo "   1. Open http://localhost:5173"
echo "   2. Click 'AI Opportunities' tab"
echo "   3. Click 'Scan 20 Stocks' button"
echo "   4. Wait for AI analysis to complete"
echo "   5. View opportunities with scores & signals!"
echo ""
echo "🔧 Logs:"
echo "   • Backend:  tail -f backend.log"
echo "   • Frontend: tail -f frontend.log"
echo ""
echo "🛑 To stop: pkill -f 'uvicorn.*8000' && pkill -f 'vite.*5173'"
echo ""
echo "🚀 Ready for AI-powered stock analysis!"

# Keep script running to show logs
echo "📊 Showing live backend logs (Ctrl+C to exit):"
tail -f backend.log 