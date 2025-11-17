"""Tool router for Local MCP Server.

Routes tool calls to their respective implementations.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("LocalMCPServer")


def route_tool_call(
    tool_name: str,
    arguments: Dict[str, Any],
    request_id: Optional[Any] = None
) -> Dict[str, Any]:
    """Route a tool call to the appropriate implementation.
    
    Args:
        tool_name: Name of the tool to invoke (e.g., 'gmail.send', 'pushover.send').
        arguments: Tool-specific arguments.
        request_id: Optional request ID for logging context.
        
    Returns:
        dict: Tool execution result.
        
    Raises:
        ValueError: If tool is not found or arguments are invalid.
        Exception: If tool execution fails.
    """
    logger.debug(f"[request_id={request_id}] Routing tool call: {tool_name}")
    
    # Import tool implementations
    try:
        from llm.local_mcp.tools.gmail_tool import gmail_send
        from llm.local_mcp.tools.pushover_tool import pushover_send
    except ImportError as e:
        logger.error(
            f"[request_id={request_id}] Failed to import tool implementations: {e}"
        )
        raise ValueError(f"Tool implementation not available: {e}")
    
    # Route to appropriate tool
    if tool_name == 'gmail.send':
        return gmail_send(arguments, request_id)
    elif tool_name == 'pushover.send':
        return pushover_send(arguments, request_id)
    else:
        logger.error(f"[request_id={request_id}] Unknown tool: {tool_name}")
        raise ValueError(f"Unknown tool: {tool_name}. Supported tools: gmail.send, pushover.send")
