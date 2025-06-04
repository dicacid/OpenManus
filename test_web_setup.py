#!/usr/bin/env python3
"""
Test script to verify OpenManus web setup
"""

import os
import sys


def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")

    try:
        import flask

        print("✅ Flask imported successfully")
    except ImportError as e:
        print(f"❌ Flask import failed: {e}")
        return False

    try:
        import flask_cors

        print("✅ Flask-CORS imported successfully")
    except ImportError as e:
        print(f"❌ Flask-CORS import failed: {e}")
        return False

    try:
        from app.agent.manus import Manus

        print("✅ Manus agent imported successfully")
    except ImportError as e:
        print(f"❌ Manus agent import failed: {e}")
        return False

    try:
        from app.agent.mcp import MCPAgent

        print("✅ MCP agent imported successfully")
    except ImportError as e:
        print(f"❌ MCP agent import failed: {e}")
        return False

    try:
        from app.agent.data_analysis import DataAnalysis

        print("✅ Data Analysis agent imported successfully")
    except ImportError as e:
        print(f"❌ Data Analysis agent import failed: {e}")
        return False

    return True


def test_config():
    """Test configuration setup"""
    print("\n🔧 Testing configuration...")

    if os.path.exists("config/config.toml"):
        print("✅ config.toml found")
        return True
    else:
        print("⚠️  config.toml not found (this is okay for testing)")
        if os.path.exists("config/config.example.toml"):
            print("✅ config.example.toml found")
        else:
            print("❌ config.example.toml not found")
            return False
        return True


def test_templates():
    """Test template files"""
    print("\n📄 Testing templates...")

    if os.path.exists("templates/index.html"):
        print("✅ index.html template found")
        return True
    else:
        print("❌ index.html template not found")
        return False


def main():
    """Main test function"""
    print("🚀 OpenManus Web Setup Test")
    print("=" * 40)

    # Check if we're in the right directory
    if not os.path.exists("app"):
        print("❌ Error: Please run this script from the OpenManus root directory")
        sys.exit(1)

    all_tests_passed = True

    # Run tests
    all_tests_passed &= test_imports()
    all_tests_passed &= test_config()
    all_tests_passed &= test_templates()

    print("\n" + "=" * 40)
    if all_tests_passed:
        print("✅ All tests passed! You can now run the web server with:")
        print("   python run_web.py")
        print("\n🌐 The web interface will be available at:")
        print("   http://localhost:8080")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        print("\n💡 Common fixes:")
        print("   - Install missing packages: pip install flask flask-cors")
        print("   - Make sure you're in the OpenManus root directory")
        print("   - Copy config.example.toml to config.toml")


if __name__ == "__main__":
    main()
