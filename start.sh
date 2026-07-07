#!/bin/bash

echo "====================================="
echo " Starting Campus ANPR System "
echo "====================================="

# Start Backend
echo "[1/2] Starting FastAPI Backend on Port 8000..."
cd backend
source venv/bin/activate
cd ..
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Start Frontend
echo "[2/2] Starting React Frontend on Port 5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "====================================="
echo " System is running! "
echo " Dashboard: http://localhost:5173 "
echo " Backend:   http://localhost:8000 "
echo " Press Ctrl+C to stop all servers "
echo "====================================="

# Trap Ctrl+C (SIGINT) and kill background processes
trap "echo -e '\nShutting down servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM

# Wait indefinitely until interrupted
wait
