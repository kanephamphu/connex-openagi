#!/bin/bash

# Set terminal title
echo -ne "\033]0;SmolLM Sub-Brain Server\007"

echo "Checking environment..."

# Declare virtual environment directory
VENV_DIR="venv"

# Use venv python if it exists, otherwise fall back to system
if [ -f "$VENV_DIR/bin/python" ]; then
    PYTHON_CMD="$VENV_DIR/bin/python"
else
    PYTHON_CMD="python3"
    if ! command -v $PYTHON_CMD &> /dev/null; then
        PYTHON_CMD="python"
    fi
fi

$PYTHON_CMD -c "import torch" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[ERROR] Torch is not installed."
    echo "Please run ./install_dependencies.sh first."
    exit 1
fi

echo "Starting SmolLM Sub-Brain Server..."
export PYTHONPATH=.
$PYTHON_CMD agi/services/smol_brain_server.py
