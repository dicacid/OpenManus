#!/usr/bin/env python3
"""
Simple startup script for OpenManus
This will check dependencies and start the main interface
"""

import sys
import subprocess
import os

def check_dependencies():
    """Check if main dependencies are available"""
    try:
        import asyncio
        from app.agent.manus import Manus
        from app.logger import logger
        print("✓ All dependencies are available!")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Installing dependencies...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✓ Dependencies installed successfully!")
            return True
        except subprocess.CalledProcessError:
            print("✗ Failed to install dependencies")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    print("🚀 Starting OpenManus...")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("main.py"):
        print("✗ Please run this script from the OpenManus root directory")
        return
    
    # Check dependencies
    if not check_dependencies():
        print("✗ Cannot start OpenManus due to dependency issues")
        return
    
    print("\n🎯 Starting OpenManus Command Line Interface...")
    print("You can enter your prompts and OpenManus will process them.")
    print("Press Ctrl+C to exit.\n")
    
    try:
        # Run the main OpenManus interface
        subprocess.run([sys.executable, "main.py"])
    except KeyboardInterrupt:
        print("\n👋 OpenManus stopped by user")
    except Exception as e:
        print(f"✗ Error running OpenManus: {e}")

if __name__ == "__main__":
    main()