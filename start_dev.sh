#!/bin/bash
# Start both backend and frontend for local development

echo "🚀 Starting MLB Trade Analyzer MVP"
echo "===================================="
echo ""

# Kill any existing servers
echo "Stopping existing servers..."
pkill -f "mvp_main.py" 2>/dev/null
pkill -f "next dev" 2>/dev/null
sleep 1

# Start backend
echo "1️⃣ Starting backend on http://localhost:8000"
cd "$(dirname "$0")"
python3 backend/mvp_main.py &
BACKEND_PID=$!
sleep 2

# Check backend
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "   ✅ Backend is running!"
else
    echo "   ❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start frontend
echo ""
echo "2️⃣ Starting frontend on http://localhost:3000"
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "=================================="
echo "✅ Servers started!"
echo ""
echo "📡 Backend:  http://localhost:8000"
echo "🌐 Frontend: http://localhost:3000 (will open in ~30 seconds)"
echo ""
echo "Press Ctrl+C to stop both servers"
echo "=================================="

# Wait for Ctrl+C
trap "echo ''; echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Done!'; exit" INT
wait
