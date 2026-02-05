#!/bin/bash

echo -ne "\033]0;Sub-Brain Parallel Demo\007"
echo "Starting Sub-Brain Parallel Demo..."

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

export PYTHONPATH=.
echo ""
$PYTHON_CMD tests/demo_sub_brain.py
