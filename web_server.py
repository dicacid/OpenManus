#!/usr/bin/env python3
"""
OpenManus Web Server
A simple web interface for OpenManus AI agents
"""

import asyncio
import json
import logging
import queue
import threading
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from flask import Flask, Response, jsonify, render_template, request
from flask_cors import CORS

from app.agent.data_analysis import DataAnalysis
from app.agent.manus import Manus
from app.agent.mcp import MCPAgent
from app.config import config
from app.logger import logger

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

# Global variables for managing agents and sessions
active_sessions: Dict[str, Dict[str, Any]] = {}
agent_types = {"manus": Manus, "mcp": MCPAgent, "data_analysis": DataAnalysis}


class WebManusSession:
    """Manages a single user session with an OpenManus agent"""

    def __init__(self, session_id: str, agent_type: str = "manus"):
        self.session_id = session_id
        self.agent_type = agent_type
        self.agent: Optional[Any] = None
        self.message_queue = queue.Queue()
        self.is_processing = False
        self.created_at = datetime.now()

    async def initialize_agent(self):
        """Initialize the selected agent type"""
        try:
            if self.agent_type == "manus":
                self.agent = await Manus.create()
            elif self.agent_type == "mcp":
                self.agent = MCPAgent()
                await self.agent.initialize(connection_type="stdio")
            elif self.agent_type == "data_analysis":
                self.agent = DataAnalysis()
            else:
                raise ValueError(f"Unknown agent type: {self.agent_type}")

            logger.info(
                f"Initialized {self.agent_type} agent for session {self.session_id}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            return False

    async def process_message(self, message: str) -> str:
        """Process a message with the agent"""
        if not self.agent:
            return "Error: Agent not initialized"

        try:
            self.is_processing = True
            response = await self.agent.run(message)
            return response if response else "Agent completed the task successfully."
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"Error: {str(e)}"
        finally:
            self.is_processing = False

    async def cleanup(self):
        """Clean up agent resources"""
        if self.agent and hasattr(self.agent, "cleanup"):
            await self.agent.cleanup()


@app.route("/")
def index():
    """Main page"""
    return render_template("index.html")


@app.route("/api/session/create", methods=["POST"])
def create_session():
    """Create a new agent session"""
    try:
        data = request.get_json() or {}
        agent_type = data.get("agent_type", "manus")

        if agent_type not in agent_types:
            return jsonify({"error": f"Invalid agent type: {agent_type}"}), 400

        session_id = str(uuid.uuid4())
        session = WebManusSession(session_id, agent_type)
        active_sessions[session_id] = session

        # Initialize agent in background
        def init_agent():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(session.initialize_agent())
            if not success:
                active_sessions.pop(session_id, None)

        threading.Thread(target=init_agent, daemon=True).start()

        return jsonify(
            {
                "session_id": session_id,
                "agent_type": agent_type,
                "status": "initializing",
            }
        )

    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/session/<session_id>/status")
def session_status(session_id: str):
    """Get session status"""
    session = active_sessions.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    return jsonify(
        {
            "session_id": session_id,
            "agent_type": session.agent_type,
            "is_processing": session.is_processing,
            "agent_ready": session.agent is not None,
            "created_at": session.created_at.isoformat(),
        }
    )


@app.route("/api/session/<session_id>/chat", methods=["POST"])
def chat(session_id: str):
    """Send a message to the agent"""
    session = active_sessions.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    if not session.agent:
        return jsonify({"error": "Agent not ready yet"}), 400

    if session.is_processing:
        return jsonify({"error": "Agent is currently processing another request"}), 429

    try:
        data = request.get_json()
        message = data.get("message", "").strip()

        if not message:
            return jsonify({"error": "Message cannot be empty"}), 400

        # Process message in background and return immediately
        def process_message():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(session.process_message(message))
            session.message_queue.put(
                {
                    "type": "response",
                    "content": response,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        threading.Thread(target=process_message, daemon=True).start()

        return jsonify(
            {"status": "processing", "message": "Request submitted successfully"}
        )

    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/session/<session_id>/messages")
def get_messages(session_id: str):
    """Get pending messages from the agent"""
    session = active_sessions.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    messages = []
    while not session.message_queue.empty():
        try:
            messages.append(session.message_queue.get_nowait())
        except queue.Empty:
            break

    return jsonify({"messages": messages, "is_processing": session.is_processing})


@app.route("/api/session/<session_id>/close", methods=["POST"])
def close_session(session_id: str):
    """Close a session and cleanup resources"""
    session = active_sessions.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    def cleanup():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(session.cleanup())

    threading.Thread(target=cleanup, daemon=True).start()
    active_sessions.pop(session_id, None)

    return jsonify({"status": "Session closed successfully"})


@app.route("/api/agents")
def list_agents():
    """List available agent types"""
    return jsonify(
        {
            "agents": [
                {
                    "type": "manus",
                    "name": "OpenManus Agent",
                    "description": "General-purpose AI agent for various tasks",
                },
                {
                    "type": "mcp",
                    "name": "MCP Agent",
                    "description": "Model Context Protocol agent with enhanced tool support",
                },
                {
                    "type": "data_analysis",
                    "name": "Data Analysis Agent",
                    "description": "Specialized agent for data analysis and visualization",
                },
            ]
        }
    )


@app.route("/health")
def health_check():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "active_sessions": len(active_sessions),
            "timestamp": datetime.now().isoformat(),
        }
    )


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    print("🚀 Starting OpenManus Web Server...")
    print("📍 Server will be available at: http://localhost:8080")
    print("🔧 Available agents: Manus, MCP, Data Analysis")
    print("💡 Use Ctrl+C to stop the server")

    try:
        app.run(host="0.0.0.0", port=8080, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n👋 Shutting down OpenManus Web Server...")
        # Cleanup all active sessions
        for session in active_sessions.values():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(session.cleanup())
            except Exception as e:
                logger.error(f"Error cleaning up session: {e}")
        print("✅ Server stopped successfully")
