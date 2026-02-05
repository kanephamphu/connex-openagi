@echo off
echo Installing SmolLM Sub-Brain Dependencies...
echo This may take a few minutes as Torch is large.
echo.

:: Install Torch with CUDA 12.1 support (recommended for SmolLM)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

:: Install other requirements
pip install bitsandbytes accelerate transformers fastapi uvicorn httpx

echo.
echo Installation complete! 
echo You can now run run_smol_brain.bat
pause
