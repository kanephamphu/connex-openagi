#!/bin/bash

echo "=========================================="
echo "AGI World Model Training: Cognition Phase"
echo "=========================================="
echo "Dataset Directory: agi/world/datasets"
echo "Model Persistence: models/world_model.pth"
echo ""

# Detect python
PYTHON_CMD="python3"
if ! command -v $PYTHON_CMD &> /dev/null; then
    PYTHON_CMD="python"
fi

if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "[ERROR] Python not found. Please install Python 3.10+"
    exit 1
fi

echo "Starting modular training loop..."
$PYTHON_CMD -u agi/world/metaphysical/train_world.py --epochs 100

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Training failed. Check datasets and torch installation."
    exit 1
fi

echo ""
echo "[SUCCESS] World Cognition matured and saved to models/world_model.pth"
echo ""
