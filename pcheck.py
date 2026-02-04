import sys
with open('python_check.txt', 'w') as f:
    f.write(f"Python Version: {sys.version}\n")
    f.write(f"Executable: {sys.executable}\n")
