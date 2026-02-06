@echo off
set "PYTHON_UNBUFFERED=1"
python -u tests/test_world_layer_v2.py > test_verification.log 2>&1
echo Done.
