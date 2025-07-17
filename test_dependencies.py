#!/usr/bin/env python3
"""Quick test to check if main dependencies are available"""

try:
    import asyncio
    print("✓ asyncio available")
    
    from app.agent.manus import Manus
    print("✓ Manus agent available")
    
    from app.logger import logger
    print("✓ Logger available")
    
    print("\n✓ All main dependencies are available!")
    print("OpenManus should be ready to run.")
    
except ImportError as e:
    print(f"✗ Missing dependency: {e}")
    print("Please run: pip install -r requirements.txt")
except Exception as e:
    print(f"✗ Error: {e}")