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

# 2. Start Smol Brain in background
echo "Starting SmolLM Sub-Brain Server in background..."
chmod +x run_smol_brain.sh
./run_smol_brain.sh > smol_brain.log 2>&1 &
echo "Smol Brain started (logging to smol_brain.log)."

# 3. Build UI
echo "Building UI..."
cd ui
npm install && npm run build
cd ..

# 4. Start App
echo "Starting AGI server..."
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
