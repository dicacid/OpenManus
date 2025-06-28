#!/usr/bin/env python3
"""
OpenManus Agent Builder Web Application
A comprehensive tool for creating, configuring, and deploying custom AI agents
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, render_template, request, send_file
from flask_cors import CORS

from app.agent.base import BaseAgent
from app.agent.toolcall import ToolCallAgent
from app.config import config
from app.llm import LLM
from app.logger import logger
from app.tool import (
    BaseTool,
    Bash,
    BrowserUseTool,
    CreateChatCompletion,
    PlanningTool,
    PythonExecute,
    StrReplaceEditor,
    Terminate,
    ToolCollection,
    WebSearch,
)

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

# Global storage for agent configurations and instances
agent_configs: Dict[str, Dict[str, Any]] = {}
agent_instances: Dict[str, BaseAgent] = {}

# Available tools registry
AVAILABLE_TOOLS = {
    "python_execute": {
        "class": PythonExecute,
        "name": "Python Execute",
        "description": "Execute Python code safely with timeout and safety restrictions",
        "category": "development",
        "icon": "🐍"
    },
    "bash": {
        "class": Bash,
        "name": "Bash Terminal",
        "description": "Execute bash commands in the terminal",
        "category": "system",
        "icon": "💻"
    },
    "str_replace_editor": {
        "class": StrReplaceEditor,
        "name": "File Editor",
        "description": "Create, view, and edit files with advanced text manipulation",
        "category": "development",
        "icon": "📝"
    },
    "browser_use": {
        "class": BrowserUseTool,
        "name": "Browser Automation",
        "description": "Automate web browsing and interaction with websites",
        "category": "web",
        "icon": "🌐"
    },
    "web_search": {
        "class": WebSearch,
        "name": "Web Search",
        "description": "Search the web for real-time information",
        "category": "web",
        "icon": "🔍"
    },
    "planning": {
        "class": PlanningTool,
        "name": "Planning Tool",
        "description": "Create and manage plans for complex tasks",
        "category": "productivity",
        "icon": "📋"
    },
    "create_chat_completion": {
        "class": CreateChatCompletion,
        "name": "Chat Completion",
        "description": "Create structured completions with specified output formatting",
        "category": "ai",
        "icon": "💬"
    },
    "terminate": {
        "class": Terminate,
        "name": "Terminate",
        "description": "Terminate the interaction when tasks are complete",
        "category": "control",
        "icon": "🛑"
    }
}

# Agent templates
AGENT_TEMPLATES = {
    "general": {
        "name": "General Purpose Agent",
        "description": "A versatile agent for various tasks",
        "tools": ["python_execute", "str_replace_editor", "web_search", "terminate"],
        "system_prompt": "You are a helpful AI assistant that can execute code, edit files, search the web, and help with various tasks.",
        "max_steps": 20,
        "temperature": 0.7
    },
    "developer": {
        "name": "Software Developer Agent",
        "description": "Specialized for software development tasks",
        "tools": ["python_execute", "bash", "str_replace_editor", "web_search", "terminate"],
        "system_prompt": "You are an expert software developer. You can write, debug, and test code, manage files, and research programming solutions.",
        "max_steps": 30,
        "temperature": 0.3
    },
    "researcher": {
        "name": "Research Agent",
        "description": "Focused on research and information gathering",
        "tools": ["web_search", "str_replace_editor", "python_execute", "terminate"],
        "system_prompt": "You are a research specialist. You excel at finding information, analyzing data, and creating comprehensive reports.",
        "max_steps": 25,
        "temperature": 0.5
    },
    "automation": {
        "name": "Automation Agent",
        "description": "Designed for web automation and browser tasks",
        "tools": ["browser_use", "web_search", "str_replace_editor", "terminate"],
        "system_prompt": "You are an automation expert. You can control web browsers, interact with websites, and automate online tasks.",
        "max_steps": 20,
        "temperature": 0.4
    },
    "planner": {
        "name": "Planning Agent",
        "description": "Specialized in task planning and project management",
        "tools": ["planning", "str_replace_editor", "web_search", "terminate"],
        "system_prompt": "You are a project planning expert. You excel at breaking down complex tasks, creating detailed plans, and managing project workflows.",
        "max_steps": 15,
        "temperature": 0.6
    }
}


class CustomAgent(ToolCallAgent):
    """Custom agent class for user-created agents"""
    
    def __init__(self, config_data: Dict[str, Any]):
        # Initialize with custom configuration
        self.name = config_data.get("name", "custom_agent")
        self.description = config_data.get("description", "A custom AI agent")
        self.system_prompt = config_data.get("system_prompt", "You are a helpful AI assistant.")
        self.max_steps = config_data.get("max_steps", 20)
        
        # Initialize LLM with custom settings
        llm_config = config_data.get("llm_config", {})
        self.llm = LLM(
            config_name="default",
            llm_config=None  # Use default config
        )
        
        # Set up tools
        tool_names = config_data.get("tools", ["terminate"])
        tools = []
        for tool_name in tool_names:
            if tool_name in AVAILABLE_TOOLS:
                tool_class = AVAILABLE_TOOLS[tool_name]["class"]
                tools.append(tool_class())
        
        self.available_tools = ToolCollection(*tools)
        self.special_tool_names = ["terminate"]
        
        # Initialize parent class
        super().__init__()


@app.route("/")
def index():
    """Main agent builder interface"""
    return render_template("agent_builder.html")


@app.route("/api/tools")
def get_available_tools():
    """Get list of available tools"""
    tools_data = []
    for tool_id, tool_info in AVAILABLE_TOOLS.items():
        tools_data.append({
            "id": tool_id,
            "name": tool_info["name"],
            "description": tool_info["description"],
            "category": tool_info["category"],
            "icon": tool_info["icon"]
        })
    
    return jsonify({"tools": tools_data})


@app.route("/api/templates")
def get_agent_templates():
    """Get list of agent templates"""
    templates_data = []
    for template_id, template_info in AGENT_TEMPLATES.items():
        templates_data.append({
            "id": template_id,
            "name": template_info["name"],
            "description": template_info["description"],
            "tools": template_info["tools"],
            "system_prompt": template_info["system_prompt"],
            "max_steps": template_info["max_steps"],
            "temperature": template_info["temperature"]
        })
    
    return jsonify({"templates": templates_data})


@app.route("/api/agent/create", methods=["POST"])
def create_agent():
    """Create a new agent configuration"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ["name", "description", "tools"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Generate unique agent ID
        agent_id = str(uuid.uuid4())
        
        # Create agent configuration
        agent_config = {
            "id": agent_id,
            "name": data["name"],
            "description": data["description"],
            "system_prompt": data.get("system_prompt", "You are a helpful AI assistant."),
            "tools": data["tools"],
            "max_steps": data.get("max_steps", 20),
            "temperature": data.get("temperature", 0.7),
            "llm_config": data.get("llm_config", {}),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Validate tools
        for tool_name in agent_config["tools"]:
            if tool_name not in AVAILABLE_TOOLS:
                return jsonify({"error": f"Unknown tool: {tool_name}"}), 400
        
        # Store configuration
        agent_configs[agent_id] = agent_config
        
        # Save to file
        save_agent_configs()
        
        return jsonify({
            "agent_id": agent_id,
            "config": agent_config,
            "message": "Agent created successfully"
        })
        
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/agent/<agent_id>")
def get_agent(agent_id: str):
    """Get agent configuration"""
    if agent_id not in agent_configs:
        return jsonify({"error": "Agent not found"}), 404
    
    return jsonify({"config": agent_configs[agent_id]})


@app.route("/api/agent/<agent_id>", methods=["PUT"])
def update_agent(agent_id: str):
    """Update agent configuration"""
    if agent_id not in agent_configs:
        return jsonify({"error": "Agent not found"}), 404
    
    try:
        data = request.get_json()
        
        # Update configuration
        agent_config = agent_configs[agent_id]
        agent_config.update({
            "name": data.get("name", agent_config["name"]),
            "description": data.get("description", agent_config["description"]),
            "system_prompt": data.get("system_prompt", agent_config["system_prompt"]),
            "tools": data.get("tools", agent_config["tools"]),
            "max_steps": data.get("max_steps", agent_config["max_steps"]),
            "temperature": data.get("temperature", agent_config["temperature"]),
            "llm_config": data.get("llm_config", agent_config["llm_config"]),
            "updated_at": datetime.now().isoformat()
        })
        
        # Validate tools
        for tool_name in agent_config["tools"]:
            if tool_name not in AVAILABLE_TOOLS:
                return jsonify({"error": f"Unknown tool: {tool_name}"}), 400
        
        # Remove from instances if it exists (will be recreated on next use)
        if agent_id in agent_instances:
            del agent_instances[agent_id]
        
        # Save to file
        save_agent_configs()
        
        return jsonify({
            "config": agent_config,
            "message": "Agent updated successfully"
        })
        
    except Exception as e:
        logger.error(f"Error updating agent: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/agent/<agent_id>", methods=["DELETE"])
def delete_agent(agent_id: str):
    """Delete agent configuration"""
    if agent_id not in agent_configs:
        return jsonify({"error": "Agent not found"}), 404
    
    try:
        # Clean up instance if it exists
        if agent_id in agent_instances:
            agent = agent_instances[agent_id]
            if hasattr(agent, "cleanup"):
                asyncio.create_task(agent.cleanup())
            del agent_instances[agent_id]
        
        # Remove configuration
        del agent_configs[agent_id]
        
        # Save to file
        save_agent_configs()
        
        return jsonify({"message": "Agent deleted successfully"})
        
    except Exception as e:
        logger.error(f"Error deleting agent: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/agents")
def list_agents():
    """List all agent configurations"""
    agents_list = []
    for agent_id, config in agent_configs.items():
        agents_list.append({
            "id": agent_id,
            "name": config["name"],
            "description": config["description"],
            "tools": config["tools"],
            "created_at": config["created_at"],
            "updated_at": config["updated_at"]
        })
    
    return jsonify({"agents": agents_list})


@app.route("/api/agent/<agent_id>/test", methods=["POST"])
def test_agent(agent_id: str):
    """Test an agent with a sample prompt"""
    if agent_id not in agent_configs:
        return jsonify({"error": "Agent not found"}), 404
    
    try:
        data = request.get_json()
        test_prompt = data.get("prompt", "Hello! Please introduce yourself and list your capabilities.")
        
        # Create or get agent instance
        if agent_id not in agent_instances:
            agent_config = agent_configs[agent_id]
            agent_instances[agent_id] = CustomAgent(agent_config)
        
        agent = agent_instances[agent_id]
        
        # Run test in background
        def run_test():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(agent.run(test_prompt))
                return {"success": True, "result": result}
            except Exception as e:
                return {"success": False, "error": str(e)}
            finally:
                loop.close()
        
        import threading
        result_container = {}
        
        def test_thread():
            result_container.update(run_test())
        
        thread = threading.Thread(target=test_thread)
        thread.start()
        thread.join(timeout=60)  # 60 second timeout
        
        if thread.is_alive():
            return jsonify({"error": "Test timed out"}), 408
        
        if result_container.get("success"):
            return jsonify({
                "result": result_container["result"],
                "message": "Test completed successfully"
            })
        else:
            return jsonify({"error": result_container.get("error", "Unknown error")}), 500
            
    except Exception as e:
        logger.error(f"Error testing agent: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/agent/<agent_id>/export")
def export_agent(agent_id: str):
    """Export agent configuration as JSON file"""
    if agent_id not in agent_configs:
        return jsonify({"error": "Agent not found"}), 404
    
    try:
        config = agent_configs[agent_id]
        filename = f"agent_{config['name'].replace(' ', '_').lower()}_{agent_id[:8]}.json"
        
        # Create temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f, indent=2)
            temp_path = f.name
        
        return send_file(
            temp_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/json'
        )
        
    except Exception as e:
        logger.error(f"Error exporting agent: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/agent/import", methods=["POST"])
def import_agent():
    """Import agent configuration from JSON file"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Read and parse JSON
        content = file.read().decode('utf-8')
        config_data = json.loads(content)
        
        # Generate new ID
        agent_id = str(uuid.uuid4())
        
        # Update configuration
        config_data.update({
            "id": agent_id,
            "imported_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        })
        
        # Validate tools
        for tool_name in config_data.get("tools", []):
            if tool_name not in AVAILABLE_TOOLS:
                return jsonify({"error": f"Unknown tool: {tool_name}"}), 400
        
        # Store configuration
        agent_configs[agent_id] = config_data
        
        # Save to file
        save_agent_configs()
        
        return jsonify({
            "agent_id": agent_id,
            "config": config_data,
            "message": "Agent imported successfully"
        })
        
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON file"}), 400
    except Exception as e:
        logger.error(f"Error importing agent: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/agent/<agent_id>/deploy", methods=["POST"])
def deploy_agent(agent_id: str):
    """Generate deployment code for an agent"""
    if agent_id not in agent_configs:
        return jsonify({"error": "Agent not found"}), 404
    
    try:
        config = agent_configs[agent_id]
        
        # Generate Python code for the agent
        deployment_code = generate_deployment_code(config)
        
        return jsonify({
            "deployment_code": deployment_code,
            "filename": f"{config['name'].replace(' ', '_').lower()}_agent.py",
            "message": "Deployment code generated successfully"
        })
        
    except Exception as e:
        logger.error(f"Error generating deployment code: {e}")
        return jsonify({"error": str(e)}), 500


def generate_deployment_code(config: Dict[str, Any]) -> str:
    """Generate Python deployment code for an agent"""
    tools_import = []
    tools_init = []
    
    for tool_name in config["tools"]:
        if tool_name in AVAILABLE_TOOLS:
            tool_class = AVAILABLE_TOOLS[tool_name]["class"]
            class_name = tool_class.__name__
            tools_import.append(class_name)
            tools_init.append(f"{class_name}()")
    
    tools_import_str = ", ".join(tools_import)
    tools_init_str = ", ".join(tools_init)
    
    code = f'''#!/usr/bin/env python3
"""
Custom OpenManus Agent: {config["name"]}
Generated by OpenManus Agent Builder

Description: {config["description"]}
Created: {config.get("created_at", "Unknown")}
"""

import asyncio
from app.agent.toolcall import ToolCallAgent
from app.tool import {tools_import_str}, ToolCollection
from app.llm import LLM


class {config["name"].replace(" ", "")}Agent(ToolCallAgent):
    """
    {config["description"]}
    """
    
    name: str = "{config["name"].lower().replace(" ", "_")}"
    description: str = "{config["description"]}"
    system_prompt: str = """{config["system_prompt"]}"""
    
    max_steps: int = {config["max_steps"]}
    
    # Configure available tools
    available_tools: ToolCollection = ToolCollection(
        {tools_init_str}
    )
    
    special_tool_names: list[str] = ["terminate"]


async def main():
    """Main function to run the agent"""
    agent = {config["name"].replace(" ", "")}Agent()
    
    try:
        prompt = input("Enter your prompt: ")
        if not prompt.strip():
            print("Empty prompt provided.")
            return
        
        print("Processing your request...")
        result = await agent.run(prompt)
        print("\\nResult:")
        print(result)
        
    except KeyboardInterrupt:
        print("\\nOperation interrupted.")
    except Exception as e:
        print(f"Error: {{e}}")
    finally:
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
'''
    
    return code


def save_agent_configs():
    """Save agent configurations to file"""
    try:
        os.makedirs("agent_configs", exist_ok=True)
        with open("agent_configs/agents.json", "w") as f:
            json.dump(agent_configs, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving agent configurations: {e}")


def load_agent_configs():
    """Load agent configurations from file"""
    try:
        if os.path.exists("agent_configs/agents.json"):
            with open("agent_configs/agents.json", "r") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading agent configurations: {e}")
    return {}


@app.route("/health")
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "agents_count": len(agent_configs),
        "active_instances": len(agent_instances),
        "timestamp": datetime.now().isoformat()
    })


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    # Load existing configurations
    agent_configs.update(load_agent_configs())
    
    print("🤖 Starting OpenManus Agent Builder...")
    print("📍 Server will be available at: http://localhost:8081")
    print("🛠️ Build, test, and deploy custom AI agents")
    print("💡 Use Ctrl+C to stop the server")
    
    try:
        app.run(host="0.0.0.0", port=8081, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n👋 Shutting down Agent Builder...")
        # Cleanup all active instances
        for agent in agent_instances.values():
            try:
                if hasattr(agent, "cleanup"):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(agent.cleanup())
            except Exception as e:
                logger.error(f"Error cleaning up agent: {e}")
        print("✅ Server stopped successfully")