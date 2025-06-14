"""
Mock implementation of BrowserUseTool for demonstration purposes.
This replaces the browser-use dependency which requires Python 3.11+.
"""
import asyncio
import json
from typing import Optional

from app.tool.base import BaseTool, ToolResult


class BrowserUseTool(BaseTool):
    """Mock browser automation tool for demonstration."""
    
    name: str = "browser_use"
    description: str = "Mock browser automation tool (browser-use requires Python 3.11+)"
    parameters: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["go_to_url", "click_element", "input_text", "scroll_down", "scroll_up"],
                "description": "The browser action to perform",
            },
            "url": {"type": "string", "description": "URL for go_to_url action"},
            "text": {"type": "string", "description": "Text for input_text action"},
        },
        "required": ["action"],
    }
    
    async def execute(self, **kwargs) -> ToolResult:
        """Mock browser execution."""
        action = kwargs.get("action")
        url = kwargs.get("url", "")
        text = kwargs.get("text", "")
        
        if action == "go_to_url":
            return ToolResult(
                output=f"Mock: Would navigate to {url}\n"
                       f"Note: Browser automation requires Python 3.11+ for browser-use package."
            )
        elif action == "click_element":
            return ToolResult(output="Mock: Would click element")
        elif action == "input_text":
            return ToolResult(output=f"Mock: Would input text: {text}")
        elif action in ["scroll_down", "scroll_up"]:
            return ToolResult(output=f"Mock: Would {action}")
        else:
            return ToolResult(error=f"Unknown action: {action}")
    
    async def cleanup(self):
        """Mock cleanup."""
        pass
