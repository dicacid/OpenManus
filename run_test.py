#!/usr/bin/env python3
import subprocess
import sys

print("Testing OpenManus dependencies...")
result = subprocess.run([sys.executable, "test_dependencies.py"], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("Errors:", result.stderr)