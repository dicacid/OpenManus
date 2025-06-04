import asyncio

from flask import Flask, jsonify, render_template, request

from app.agent.manus import Manus

app = Flask(__name__)
agent = None


def init_agent():
    global agent
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    agent = loop.run_until_complete(Manus.create())
    return loop


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process():
    prompt = request.json.get("prompt", "")
    if not prompt.strip():
        return jsonify({"error": "Empty prompt provided"})

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    response = loop.run_until_complete(agent.run(prompt))
    return jsonify({"response": response})


if __name__ == "__main__":
    init_agent()
    app.run(host="0.0.0.0", port=8080)  #!/usr/bin/env python3
"""
OpenManus Web Server Launcher
Simple script to start the OpenManus web interface
"""

import os
import subprocess
import sys


def check_requirements():
    """Check if required packages are installed"""
    try:
        import flask
        import flask_cors

        print("✅ Flask dependencies found")
        return True
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("📦 Installing required packages...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "flask", "flask-cors"]
            )
            print("✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            return False


def main():
    """Main function to start the web server"""
    print("🚀 OpenManus Web Server Launcher")
    print("=" * 40)

    # Check if we're in the right directory
    if not os.path.exists("app"):
        print("❌ Error: Please run this script from the OpenManus root directory")
        print("💡 Make sure you're in the directory containing the 'app' folder")
        sys.exit(1)

    # Check requirements
    if not check_requirements():
        print("❌ Cannot start server due to missing dependencies")
        sys.exit(1)

    # Check config
    if not os.path.exists("config/config.toml"):
        print("⚠️  Warning: config/config.toml not found")
        print(
            "📝 Please copy config/config.example.toml to config/config.toml and add your API keys"
        )
        print(
            "🔧 You can still start the server, but agents may not work without proper configuration"
        )
        input("Press Enter to continue anyway, or Ctrl+C to exit...")

    print("\n🌐 Starting OpenManus Web Server...")
    print("📍 Server will be available at: http://localhost:8080")
    print("🛑 Press Ctrl+C to stop the server\n")

    try:
        # Import and run the web server
        from web_server import app

        app.run(host="0.0.0.0", port=8080, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n👋 Shutting down OpenManus Web Server...")
        print("✅ Server stopped successfully")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
