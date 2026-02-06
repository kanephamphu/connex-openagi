import sys
import os
print(f"Current Dir: {os.getcwd()}")
try:
    import agi
    print("AGI imported successfully")
except Exception as e:
    print(f"Import failed: {e}")
