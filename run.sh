#!/bin/bash

# run.sh - Deployment Script for Connex AGI

# 1. Kill current server on port 8001
echo "Stopping current server on port 8001..."
PORT=8001
PID=$(lsof -t -i:$PORT)
if [ -n "$PID" ]; then
  kill -9 $PID
  echo "Server stopped (PID: $PID)"
else
  echo "No server running on port $PORT"
fi

# 2. Build UI
echo "Building UI..."
cd ui
npm install && npm run build
cd ..

# 3. Start App
echo "Starting AGI server..."
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
