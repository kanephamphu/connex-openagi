#!/bin/bash

echo "Installing SmolLM Sub-Brain Dependencies for macOS..."
echo "This may take a few minutes as Torch is a large package."

# Detect python command
PYTHON_CMD="python3"
if ! command -v $PYTHON_CMD &> /dev/null; then
    PYTHON_CMD="python"
fi

# Declare virtual environment directory
VENV_DIR="venv"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR..."
    $PYTHON_CMD -m venv $VENV_DIR
fi

# Use venv's pip
PIP_CMD="$VENV_DIR/bin/pip"
VENV_PYTHON="$VENV_DIR/bin/python"

echo "Using virtual environment: $VENV_DIR"

# Upgrade pip
$PIP_CMD install --upgrade pip

# Install Project Core Dependencies
echo "Installing Project Core Dependencies..."
$PIP_CMD install -e .

# Install Torch
echo "Installing Torch..."
$PIP_CMD install torch torchvision torchaudio

# Install Other Requirements
echo "Installing LLM and Server dependencies..."
# transformers, fastapi, uvicorn, httpx are in pyproject.toml but 
# we ensure accelerate is included.
$PIP_CMD install accelerate transformers fastapi uvicorn httpx python-dotenv

echo ""
echo "Installation complete!"
echo "You can now run ./run_smol_brain.sh (it will automatically use the virtual environment)"
