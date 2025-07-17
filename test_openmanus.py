#!/usr/bin/env python3
"""
Test script to demonstrate OpenManus functionality.
"""
import asyncio
import sys
from app.agent.manus import Manus
from app.logger import logger

async def test_openmanus():
    """Test OpenManus with a simple prompt."""
    try:
        logger.info("Creating Manus agent...")
        agent = await Manus.create()
        
        logger.info("Testing available tools...")
        tools = agent.available_tools.tools
        logger.info(f"Available tools: {[tool.name for tool in tools]}")
        
        # Test with a simple prompt that doesn't require LLM API
        logger.info("Testing tool execution...")
        
        # Test Python execution tool
        python_tool = next((tool for tool in tools if tool.name == "python_execute"), None)
        if python_tool:
            result = await python_tool.execute(code="print('Hello from OpenManus!')")
            logger.info(f"Python tool result: {result}")
        
        # Test file editor tool
        editor_tool = next((tool for tool in tools if tool.name == "str_replace_editor"), None)
        if editor_tool:
            result = await editor_tool.execute(command="create", path="/tmp/test.txt", file_text="Hello OpenManus!")
            logger.info(f"Editor tool result: {result}")
        
        # Test browser tool (mock)
        browser_tool = next((tool for tool in tools if tool.name == "browser_use"), None)
        if browser_tool:
            result = await browser_tool.execute(action="go_to_url", url="https://example.com")
            logger.info(f"Browser tool result: {result}")
        
        logger.info("OpenManus test completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'agent' in locals():
            await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(test_openmanus())
