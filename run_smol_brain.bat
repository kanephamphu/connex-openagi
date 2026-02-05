@echo off
title SmolLM Sub-Brain Server
echo Checking environment...

python -c "import torch" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Torch is not installed. 
    echo Please run install_dependencies.bat first.
    pause
    exit /b
)

echo Starting SmolLM Sub-Brain Server...
set PYTHONPATH=.
python agi/services/smol_brain_server.py
pause
