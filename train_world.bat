@echo off
echo ==========================================
echo AGI World Model Training: Cognition Phase
echo ==========================================
echo Dataset Directory: agi\world\datasets
echo Model Persistence: models\world_model.pth
echo.

:: Detect python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

echo Starting modular training loop...
python -u agi\world\metaphysical\train_world.py --epochs 100

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Training failed. Check datasets and torch installation.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] World Cognition matured and saved to models\world_model.pth
echo.
pause
