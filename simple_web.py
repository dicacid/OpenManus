#!/usr/bin/env python3
"""
Simple OpenManus Web Server
A minimal web interface for OpenManus AI agent
"""

import asyncio
from flask import Flask, jsonify, render_template, request
from app.agent.manus import Manus

app = Flask(__name__)
agent = None


def init_agent():
    """Initialize the OpenManus agent"""
    global agent
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    agent = loop.run_until_complete(Manus.create())
    print("✅ OpenManus agent initialized successfully")
    return loop


@app.route("/")
def index():
    """Main page"""
    return render_template("simple_index.html")


@app.route("/process", methods=["POST"])
def process():
    """Process user message with the agent"""
    try:
        prompt = request.json.get("prompt", "")
        if not prompt.strip():
            return jsonify({"error": "Empty prompt provided"}), 400

        # Process the message with the agent
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(agent.run(prompt))
        
        return jsonify({"response": response or "Task completed successfully."})
    
    except Exception as e:
        print(f"Error processing message: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "agent_ready": agent is not None
    })


if __name__ == "__main__":
    print("🚀 Starting Simple OpenManus Web Server...")
    print("📍 Initializing agent...")
    
    try:
        init_agent()
        print("📍 Server will be available at: http://localhost:8080")
        print("🛑 Press Ctrl+C to stop the server\n")
        
        app.run(host="0.0.0.0", port=8080, debug=True)
    except KeyboardInterrupt:
        print("\n👋 Shutting down server...")
    except Exception as e:
        print(f"❌ Error: {e}")